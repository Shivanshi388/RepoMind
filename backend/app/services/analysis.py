import uuid,threading,zipfile,io
from collections import Counter
from datetime import datetime,timezone
from app.core.config import settings
from app.core.security import parse_github_url
from app.services.github import GitHubClient,GitHubError
from app.engines.analysis.filtering import eligible
from app.engines.parser.analyzer import analyze_source
JOBS={};RESULTS={};LOCK=threading.RLock()
def now():return datetime.now(timezone.utc).isoformat()
def start_analysis(url):
 owner,repo=parse_github_url(url); jid=str(uuid.uuid4())
 with LOCK:JOBS[jid]={"id":jid,"status":"queued","stage":"Queued","progress":0,"error":None,"created_at":now()}
 threading.Thread(target=_run,args=(jid,owner,repo,url),daemon=True).start()
 return {"job_id":jid,"status":"queued"}
def _run(jid,owner,repo,url):
 with LOCK:JOBS[jid].update(status="running",stage="Loading repository metadata",progress=5)
 client=GitHubClient()
 try:
  meta=client.repository(owner,repo)
  if meta.get("private"):raise GitHubError("Only public repositories are supported.",403)
  branch=meta.get("default_branch") or "main"
  from urllib.parse import quote
  commit=client.get(f"/repos/{owner}/{repo}/commits/{quote(branch,safe='')}").get("sha")
  if not commit:raise GitHubError("GitHub did not return a commit for the default branch.")
  rid=f"{owner}/{repo}@{commit}"
  with LOCK:
   if rid in RESULTS:JOBS[jid].update(status="completed",stage="Reused cached analysis",progress=100,repository_id=rid);return
   JOBS[jid].update(stage="Inspecting repository tree",progress=18)
  tree=client.tree(owner,repo,commit)
  if tree.get("truncated") or len(tree.get("tree",[]))>settings.max_repo_tree_entries:raise GitHubError("Repository tree exceeds safe analysis limits. Try a smaller repository.",413)
  entries=[x for x in tree.get("tree",[]) if x.get("type")=="blob" and eligible(x.get("path",""),x.get("size",0),settings.max_file_bytes)][:settings.max_files]
  with LOCK:JOBS[jid].update(stage="Downloading safe source archive",progress=30)
  archive=client.archive(owner,repo,commit,settings.max_total_bytes)
  contents={};total=0
  with zipfile.ZipFile(io.BytesIO(archive)) as z:
   members=[m for m in z.infolist() if not m.is_dir()];prefix=members[0].filename.split("/")[0]+"/" if members else "";allowed={e["path"] for e in entries}
   for m in members:
    path=m.filename[len(prefix):] if m.filename.startswith(prefix) else m.filename
    if path not in allowed or not eligible(path,m.file_size,settings.max_file_bytes):continue
    if total+m.file_size>settings.max_total_bytes:break
    data=z.read(m)
    if b"\0" in data[:8192]:continue
    source=data.decode("utf-8",errors="replace")
    contents[path]=source;total+=len(data)
    if len(contents)%50==0:
     with LOCK:JOBS[jid].update(progress=min(68,30+int(38*len(contents)/max(1,len(entries)))),stage=f"Reading source files ({len(contents)})")
  with LOCK:JOBS[jid].update(progress=70,stage="Parsing source code")
  analyses={};symbols=[];langs=Counter();total_complexity=0
  for index,(path,source) in enumerate(contents.items(),1):
   a=analyze_source(path,source);
   if index%50==0:
    with LOCK:JOBS[jid].update(progress=min(94,70+int(24*index/max(1,len(contents)))),stage=f"Parsing code ({index}/{len(contents)})")
   langs[a["language"]]+=len(source.encode());total_complexity+=a["complexity"]
   analyses[path]={"path":path,"filename":path.rsplit("/",1)[-1],"extension":"."+path.rsplit(".",1)[-1] if "." in path else "","language":a["language"],"size":len(source.encode()),"line_count":a["line_count"],"complexity":a["complexity"],"symbols":a["symbols"],"imports":a["imports"],"parser":a["parser"],"content":source}
   symbols.extend([{**s,"path":path,"language":a["language"]} for s in a["symbols"]])
  deps=[];known_paths=set(analyses)
  for path,item in analyses.items():
   for imp in item["imports"]:
    target=resolve_import(path,imp,known_paths)
    if target and target!=path:deps.append({"source":path,"target":target,"type":"import"})
  deps=list({(d["source"],d["target"]):d for d in deps}.values());languages={k:round(v/max(1,sum(langs.values()))*100,1) for k,v in langs.most_common()}
  result={"id":rid,"owner":owner,"name":repo,"full_name":meta.get("full_name",f"{owner}/{repo}"),"description":meta.get("description"),"html_url":meta.get("html_url",url),"default_branch":branch,"commit_sha":commit,"stars":meta.get("stargazers_count",0),"forks":meta.get("forks_count",0),"created_at":meta.get("created_at"),"updated_at":meta.get("updated_at"),"analyzed_at":now(),"file_count":len(analyses),"tree_file_count":len(entries),"symbol_count":len(symbols),"dependency_count":len(deps),"languages":languages,"files":analyses,"symbols":symbols[:10000],"dependencies":deps,"total_complexity":total_complexity}
  with LOCK:RESULTS[rid]=result;JOBS[jid].update(status="completed",stage="Analysis complete",progress=100,repository_id=rid)
 except GitHubError as e:
  with LOCK:JOBS[jid].update(status="failed",stage="Analysis failed",error=e.message,progress=100)
 except (zipfile.BadZipFile,KeyError,ValueError):
  with LOCK:JOBS[jid].update(status="failed",stage="Unreadable repository archive",error="GitHub returned an unreadable archive.",progress=100)
 except Exception:
  with LOCK:JOBS[jid].update(status="failed",stage="Analysis failed",error="Unexpected analysis error. Check backend logs and retry.",progress=100)
 finally:client.close()
def resolve_import(source,imp,paths):
 if imp.startswith("."):
  base=source.rsplit("/",1)[0] if "/" in source else ""
  parts=[]
  for part in (base+"/"+imp if base else imp).replace("\\","/").split("/"):
   if part in ("","."):continue
   if part=="..":
    if parts:parts.pop()
   else:parts.append(part)
  candidates=["/".join(parts)]
 else:
  # Absolute package/module imports resolve only when they match a source file in this checkout.
  candidate=imp.replace(".","/").lstrip("/")
  candidates=[candidate,"src/"+candidate,"backend/"+candidate]
 suffixes=("",".js",".jsx",".ts",".tsx",".py","/__init__.py","/index.js")
 for candidate in candidates:
  for suffix in suffixes:
   resolved=candidate+suffix
   if resolved in paths:return resolved
  matches=[p for p in paths if p.endswith("/"+candidate+".py") or p.endswith("/"+candidate+"/__init__.py")]
  if len(matches)==1:return matches[0]
 return None

def get_job(jid):
 with LOCK:return JOBS.get(jid)
def get_repository(rid):
 with LOCK:return RESULTS.get(rid)
def search(repo,q,limit=50):
 from app.services.intelligence import retrieve,tokens
 qterms=set(tokens(q));results=retrieve(repo,q,limit=limit)
 # Exact symbol names receive a transparent relevance boost on top of BM25.
 for item in results:
  item["line"]=item.pop("start_line");item.pop("end_line",None);item["kind"]="text"
  for symbol in repo["files"][item["path"]]["symbols"]:
   if q.lower() in symbol["name"].lower() and abs(symbol["start_line"]-item["line"])<100:
    item.update(symbol=symbol["name"],kind=symbol["type"],line=symbol["start_line"],score=item["score"]+3);break
 for path,f in repo["files"].items():
  if q.lower() in path.lower() and not any(x["path"]==path for x in results):results.append({"path":path,"line":1,"kind":"file","snippet":path,"score":2})
 return sorted(results,key=lambda x:(-x["score"],x["path"],x["line"]))[:limit]

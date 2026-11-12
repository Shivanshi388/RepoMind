import re
from urllib.parse import quote,urlparse
from fastapi import APIRouter,HTTPException,Query
from pydantic import BaseModel,Field
from app.services.analysis import get_repository
from app.services.github import GitHubClient,GitHubError
from app.services.history import collect_history
from app.services.intelligence import impact,suggestions,similarity,retrieve,debug_evidence,local_chat,review_file,review_patch,ollama_available
from app.engines.ml.risk import risk_report
router=APIRouter(prefix="/repositories",tags=["intelligence"])
def require(rid):
 r=get_repository(rid)
 if not r:raise HTTPException(404,"Analysis not found. Analyze the repository again.")
 return r
def history_or_error(repo):
 try:return collect_history(repo)
 except GitHubError as e:raise HTTPException(e.status,e.message)
@router.get("/{repo_id:path}/history")
def history(repo_id:str):
 r=require(repo_id);items=history_or_error(r)
 return {"commits":[{k:v for k,v in c.items() if k!="files"}|{"changed_file_count":len(c["files"])} for c in items],"inspected":len(items),"note":"Inspects up to 25 recent commit details; commit API limits and wording heuristics apply."}
@router.get("/{repo_id:path}/risk")
def risk(repo_id:str):
 r=require(repo_id);return risk_report(r,history_or_error(r))
@router.get("/{repo_id:path}/impact")
def impact_route(repo_id:str,path:str=Query(...,max_length=500)):
 result=impact(require(repo_id),path)
 if result is None:raise HTTPException(404,"File is not part of this analysis.")
 return result
@router.get("/{repo_id:path}/similarity")
def similarity_route(repo_id:str,path:str=Query(...,max_length=500)):
 result=similarity(require(repo_id),path)
 if result is None:raise HTTPException(404,"File is not part of this analysis.")
 return {"matches":result,"method":"token Jaccard similarity; candidate-symbol comparisons"}
@router.get("/{repo_id:path}/test-suggestions")
def tests_route(repo_id:str):
 return {"suggestions":suggestions(require(repo_id)),"note":"Suggestions only; no repository tests were executed."}
@router.get("/{repo_id:path}/semantic-search")
def semantic_search(repo_id:str,q:str=Query(...,min_length=2,max_length=300)):
 from app.core.config import settings
 return {"query":q,"results":retrieve(require(repo_id),q,limit=20,semantic=True),"semantic_available":ollama_available(),"retrieval":"BM25 lexical with optional local Ollama embedding rerank"}
class Question(BaseModel):question:str=Field(min_length=3,max_length=4000)
class ReviewRequest(BaseModel):path:str|None=Field(default=None,max_length=500)
class CompareRequest(BaseModel):base:str=Field(min_length=1,max_length=120);head:str=Field(min_length=1,max_length=120)
class PullRequestBody(BaseModel):url:str=Field(min_length=20,max_length=500)
@router.post("/{repo_id:path}/chat")
def chat(repo_id:str,body:Question):
 r=require(repo_id);evidence=retrieve(r,body.question,limit=4,semantic=True)
 if not evidence:return {"answer":"I could not find relevant repository evidence for that question.","citations":[],"model_available":False}
 answer=local_chat(body.question,evidence)
 return {"answer":answer or "Gemini is unavailable. The repository evidence is shown below; check the backend Gemini configuration.","citations":[{"path":x["path"],"start_line":x["start_line"],"end_line":x["end_line"]} for x in evidence],"model_available":bool(answer),"grounded":True}
@router.post("/{repo_id:path}/debug")
def debug(repo_id:str,body:Question):
 r=require(repo_id);result=debug_evidence(r,body.question);answer=local_chat(body.question,result["evidence"],"Provide plausible debugging hypotheses and concrete inspection steps. Label hypotheses clearly.")
 return {**result,"answer":answer,"model_available":bool(answer)}
@router.post("/{repo_id:path}/code-review")
def code_review(repo_id:str,body:ReviewRequest):
 r=require(repo_id)
 targets=[(body.path,r["files"].get(body.path))] if body.path else [(p,f) for p,f in sorted(r["files"].items(),key=lambda x:-x[1]["complexity"])[:50]]
 if body.path and not targets[0][1]:raise HTTPException(404,"File is not part of this analysis.")
 findings=[item for p,f in targets for item in review_file(p,f)]
 evidence=[]
 for p,f in targets[:8]:
  lines=f["content"].splitlines();evidence.append({"path":p,"start_line":1,"end_line":min(len(lines),80),"snippet":"\n".join(lines[:80])[:1800]})
 answer=local_chat("Review the supplied repository code. Focus on concrete maintainability and correctness concerns.",evidence,"Review observations are hypotheses; cite evidence and never claim a confirmed defect without proof.")
 return {"findings":findings,"files_reviewed":len(targets),"llm_review":answer,"model_available":bool(answer),"note":"Static checks are heuristics and do not replace human review."}
@router.post("/{repo_id:path}/compare")
def compare(repo_id:str,body:CompareRequest):
 r=require(repo_id);client=GitHubClient()
 try:
  path=f"/repos/{r['owner']}/{r['name']}/compare/{quote(body.base,safe='')}...{quote(body.head,safe='')}";data=client.get(path)
  changed=[]
  for f in data.get("files",[])[:300]:
   path=f.get("filename");changed.append({"path":path,"status":f.get("status"),"additions":f.get("additions",0),"deletions":f.get("deletions",0),"changes":f.get("changes",0),"impact":impact(r,path) if path in r["files"] else None})
  return {"base":body.base,"head":body.head,"ahead_by":data.get("ahead_by"),"behind_by":data.get("behind_by"),"total_commits":data.get("total_commits"),"files":changed,"note":"GitHub compare results are capped at 300 files; impact uses the currently analyzed graph."}
 except GitHubError as e:raise HTTPException(e.status,e.message)
 finally:client.close()
@router.post("/{repo_id:path}/pull-request")
def pull_request(repo_id:str,body:PullRequestBody):
 r=require(repo_id);u=urlparse(body.url);m=re.fullmatch(r"/([^/]+)/([^/]+)/pull/(\d+)/?",u.path)
 if u.scheme!="https" or u.hostname not in {"github.com","www.github.com"} or not m or (m.group(1).lower(),m.group(2).lower())!=(r["owner"].lower(),r["name"].lower()):raise HTTPException(422,"Enter a public pull request URL for this analyzed repository.")
 owner,name,num=m.groups();client=GitHubClient()
 try:
  pr=client.get(f"/repos/{owner}/{name}/pulls/{num}");files=client.get(f"/repos/{owner}/{name}/pulls/{num}/files?per_page=100")
  changed=[]
  for f in files:
   path=f.get("filename");changed.append({"path":path,"status":f.get("status"),"additions":f.get("additions",0),"deletions":f.get("deletions",0),"changes":f.get("changes",0),"patch_excerpt":"\n".join(f.get("patch","").splitlines()[:30]),"impact":impact(r,path) if path in r["files"] else None,"static_findings":review_patch(path,f.get("patch", ""))})
  patch_evidence=[{"path":f["path"],"start_line":1,"end_line":min(80,len(f["patch_excerpt"].splitlines())),"snippet":f["patch_excerpt"][:1600]} for f in changed if f["patch_excerpt"]][:8]
  summary=local_chat(f"Summarize public pull request #{num} changes and identify investigation or test suggestions.",patch_evidence,"Analyze only the supplied diff excerpts. Describe hypotheses, do not approve or assert defects.")
  return {"number":pr.get("number"),"title":pr.get("title"),"state":pr.get("state"),"html_url":pr.get("html_url"),"base":pr.get("base",{}).get("sha"),"head":pr.get("head",{}).get("sha"),"files":changed,"llm_summary":summary,"model_available":bool(summary),"suggestions":"Review changed files, impacted dependents, and test coverage. This is assistive analysis, not an automated approval.","caveat":"GitHub returns at most the first 100 files here; static checks inspect added patch lines only."}
 except GitHubError as e:raise HTTPException(e.status,e.message)
 finally:client.close()

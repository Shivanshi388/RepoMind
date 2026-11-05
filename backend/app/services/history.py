import re, threading
from app.services.github import GitHubClient,GitHubError
_HISTORY={};_LOCK=threading.Lock()
BUG=re.compile(r"\b(fix|fixes|fixed|bug|patch|regression|hotfix|correct)\b",re.I)
def collect_history(repo):
 key=repo["id"]
 with _LOCK:
  if key in _HISTORY:return _HISTORY[key]
 client=GitHubClient()
 try:
  commits=client.get(f"/repos/{repo['owner']}/{repo['name']}/commits?per_page=30&sha={repo['commit_sha']}")
  records=[]
  # Cap detail calls; each detail response gives exact changed paths and line churn.
  for item in reversed(commits[:25]):
   sha=item.get("sha")
   if not sha:continue
   detail=client.get(f"/repos/{repo['owner']}/{repo['name']}/commits/{sha}")
   message=detail.get("commit",{}).get("message","").splitlines()[0]
   changed=[]
   for f in detail.get("files",[]):
    path=f.get("filename")
    if path:
     changed.append({"path":path,"additions":int(f.get("additions",0)),"deletions":int(f.get("deletions",0)),"changes":int(f.get("changes",0)),"status":f.get("status","modified")})
   records.append({"sha":sha,"date":detail.get("commit",{}).get("author",{}).get("date"),"message":message,"bug_fix_heuristic":bool(BUG.search(message)),"files":changed})
  with _LOCK:_HISTORY[key]=records
  return records
 finally:client.close()

from fastapi import APIRouter,HTTPException,Query,Request
from pydantic import BaseModel,Field
from app.core.security import parse_github_url,InvalidRepositoryURL
from app.services.analysis import start_analysis,get_job,get_repository,search
router=APIRouter(prefix="/repositories",tags=["repositories"])
class AnalyzeRequest(BaseModel):url:str=Field(min_length=8,max_length=300)
@router.post("/analyze",status_code=202)
def analyze(body:AnalyzeRequest,request:Request):
 if not request.session.get("user_id"):
  raise HTTPException(status_code=401,detail="Sign in with GitHub before analyzing a repository.")
 try:parse_github_url(body.url);return start_analysis(body.url)
 except InvalidRepositoryURL as e:raise HTTPException(422,str(e))
def require(rid):
 r=get_repository(rid)
 if not r:raise HTTPException(404,"Analysis not found. Analyze the repository again.")
 return r
@router.get("/jobs/{job_id}")
def job(job_id:str):
 j=get_job(job_id)
 if not j:raise HTTPException(404,"Analysis job not found.")
 return j
@router.get("/{repo_id:path}/files")
def files(repo_id:str):return [{k:v for k,v in f.items() if k not in {"content","symbols","imports"}} for f in require(repo_id)["files"].values()]
@router.get("/{repo_id:path}/files/content")
def content(repo_id:str,path:str=Query(...,max_length=500)):
 f=require(repo_id)["files"].get(path)
 if not f:raise HTTPException(404,"File is not in this analysis.")
 return f
@router.get("/{repo_id:path}/architecture")
def architecture(repo_id:str):
 r=require(repo_id);return {"nodes":[{"id":p,"label":p.rsplit("/",1)[-1],"path":p,"language":f["language"],"complexity":f["complexity"]} for p,f in r["files"].items()],"edges":r["dependencies"]}
@router.get("/{repo_id:path}/search")
def search_route(repo_id:str,q:str=Query(...,min_length=1,max_length=200)):return {"results":search(require(repo_id),q)}
@router.get("/{repo_id:path}/insights")
def insights(repo_id:str):
 r=require(repo_id);fs=list(r["files"].values());incoming={}
 for d in r["dependencies"]:incoming[d["target"]]=incoming.get(d["target"],0)+1
 return {"large_files":[{"path":x["path"],"line_count":x["line_count"]} for x in sorted(fs,key=lambda x:x["line_count"],reverse=True)[:5]],"complex_files":[{"path":x["path"],"complexity":x["complexity"]} for x in sorted(fs,key=lambda x:x["complexity"],reverse=True)[:5]],"connected_files":[{"path":p,"incoming":v} for p,v in sorted(incoming.items(),key=lambda x:-x[1])[:5]],"caveat":"Complexity is a deterministic static estimate, not a defect prediction."}

@router.get("/{repo_id:path}")
def overview(repo_id:str):return {k:v for k,v in require(repo_id).items() if k not in {"files","symbols","dependencies"}}


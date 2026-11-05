from collections import Counter,defaultdict
from app.services.history import BUG

def risk_report(repo,history):
 files=repo["files"];inbound=Counter(e["target"] for e in repo["dependencies"]);stats=defaultdict(lambda:{"changes":0,"churn":0,"bugfix_touches":0,"last":None})
 for i,commit in enumerate(history):
  for f in commit["files"]:
   s=stats[f["path"]];s["changes"]+=1;s["churn"]+=f["additions"]+f["deletions"];s["last"]=i
   if commit["bug_fix_heuristic"]:s["bugfix_touches"]+=1
 paths=list(files);records=[stats[p] for p in paths]
 snapshots=[];n=len(history)
 # Time-ordered snapshots: features use preceding commits only, labels use a later window.
 for i in range(3,n-3,2):
  prev=history[:i];future=history[i:min(n,i+4)];counts=Counter();churn=Counter();last={};bug_future=set()
  for j,c in enumerate(prev):
   for f in c["files"]:counts[f["path"]]+=1;churn[f["path"]]+=f["additions"]+f["deletions"];last[f["path"]]=j
  for c in future:
   if c["bug_fix_heuristic"]:bug_future.update(f["path"] for f in c["files"])
  rows=[]
  for path in paths:
   f=files[path];age=i-last[path] if path in last else i+1
   x=[counts[path],churn[path],age]
   rows.append((x,int(path in bug_future)))
  snapshots.append((i,rows))
 result=[]
 for path,f in files.items():
  st=stats[path];age=(n-1-st["last"]) if st["last"] is not None else n
  x=[st["changes"],st["churn"],age]
  score=min(100,12*min(f["complexity"],15)+8*min(st["changes"],5)+0.02*min(st["churn"],1000)+5*min(inbound[path],5))
  result.append({"path":path,"features":{"historical_changes":st["changes"],"historical_churn":st["churn"],"bug_fix_commit_touches":st["bugfix_touches"],"commits_since_last_change":age,"complexity_estimate":f["complexity"],"incoming_dependencies":inbound[path]},"baseline_score":round(score,1),"score":round(score,1),"score_type":"transparent heuristic","risk_level":"high" if score>=75 else "medium" if score>=40 else "low","evidence":[x for x in [f"{st['changes']} changes among inspected commits",f"{st['bugfix_touches']} heuristic bug-fix commit touches",f"complexity estimate {f['complexity']}",f"{inbound[path]} incoming file dependencies"] if not x.startswith("0 ")]})
 model_info={"trained":False,"reason":"History is too small or lacks both outcome classes.","train_test_split":"time ordered","label_note":"A commit-message bug-fix heuristic is a noisy proxy, not a verified defect label."}
 if len(snapshots)>=5:
  cutoff=int(n*0.7)
  # Purge snapshots whose forward-label window overlaps the temporal holdout.
  train=[row for i,rows in snapshots if i+4<=cutoff for row in rows]
  test=[row for i,rows in snapshots if i>=cutoff for row in rows]
  if sum(y for _,y in train)>=3 and sum(y for _,y in test)>=1 and len({y for _,y in train})==2:
   try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import average_precision_score,precision_recall_fscore_support
    from sklearn.preprocessing import StandardScaler
    import numpy as np
    X=np.asarray([x for x,y in train],dtype=float);Y=np.asarray([y for x,y in train]);Xt=np.asarray([x for x,y in test],dtype=float);Yt=np.asarray([y for x,y in test])
    scaler=StandardScaler();X=scaler.fit_transform(X);Xt=scaler.transform(Xt);model=LogisticRegression(class_weight="balanced",max_iter=500).fit(X,Y)
    pred=model.predict(Xt);score=model.decision_function(Xt);pr,rc,f1,_=precision_recall_fscore_support(Yt,pred,average="binary",zero_division=0)
    k=max(1,int(Yt.sum()));baseline=np.zeros(len(Yt),dtype=int);baseline[np.argsort(Xt[:,1])[-k:]]=1
    bpr,brc,bf1,_=precision_recall_fscore_support(Yt,baseline,average="binary",zero_division=0)
    mapping={}
    for path,f in files.items():
     st=stats[path];age=n-1-st["last"] if st["last"] is not None else n
     mapping[path]=[st["changes"],st["churn"],age]
    probs=model.predict_proba(scaler.transform([mapping[x["path"]] for x in result]))[:,1]
    for item,value in zip(result,probs):item["score"]=round(float(value)*100,1);item["score_type"]="relative model ranking (not a calibrated probability)"
    model_info={"trained":True,"model":"LogisticRegression","time_ordered_snapshots":len(snapshots),"time_cutoff_commit_index":cutoff,"purge_gap_commits":4,"training_examples":len(train),"test_examples":len(test),"test_positive_rate":round(float(Yt.mean()),3),"precision":round(float(pr),3),"recall":round(float(rc),3),"f1":round(float(f1),3),"pr_auc":round(float(average_precision_score(Yt,score)),3),"churn_baseline":{"precision":round(float(bpr),3),"recall":round(float(brc),3),"f1":round(float(bf1),3)},"train_test_split":"time ordered (70/30 snapshots)","label_note":"Commit-message bug-fix heuristic is a noisy proxy, not a verified defect label.","warning":"Scores rank review attention and are not calibrated probabilities of bugs."}
   except Exception as e:model_info["reason"]=f"Model training unavailable: {type(e).__name__}"
 result.sort(key=lambda x:-x["score"])
 return {"items":result[:100],"history_commits":len(history),"model":model_info,"limitations":["Only the 25 latest commit details are inspected.","Bug-fix labels are derived from commit message wording.","Repositories with sparse history use the transparent heuristic ranking."]}

from app.services.intelligence import impact,suggestions,similarity,review_file,retrieve
from app.engines.ml.risk import risk_report

def fixture_repo():
 files={
  "src/core.py":{"path":"src/core.py","content":"def calculate_total(items):\n    total = 0\n    for item in items:\n        if item:\n            total += item\n    return total\n","line_count":6,"complexity":4,"symbols":[{"name":"calculate_total","type":"function","start_line":1,"end_line":6}]},
  "src/helper.py":{"path":"src/helper.py","content":"def calculate_sum(items):\n    total = 0\n    for item in items:\n        if item:\n            total += item\n    return total\n","line_count":6,"complexity":4,"symbols":[{"name":"calculate_sum","type":"function","start_line":1,"end_line":6}]},
  "src/api.py":{"path":"src/api.py","content":"from .core import calculate_total\n","line_count":1,"complexity":2,"symbols":[]},
  "tests/test_core.py":{"path":"tests/test_core.py","content":"def test_calculate_total(): pass\n","line_count":1,"complexity":1,"symbols":[]}}
 return {"id":"a/b@sha","files":files,"dependencies":[{"source":"src/api.py","target":"src/core.py"},{"source":"src/worker.py","target":"src/api.py"},{"source":"tests/test_core.py","target":"src/core.py"}]}
def test_impact_finds_direct_transitive_and_tests():
 r=impact(fixture_repo(),"src/core.py")
 assert {x["path"] for x in r["impacted"]}>={"src/api.py","src/worker.py"}
 assert "tests/test_core.py" in r["tests"]
def test_similarity_and_suggestions_are_labeled():
 r=fixture_repo();matches=similarity(r,"src/core.py")
 assert matches and matches[0]["match"]["path"]=="src/helper.py"
 assert all(x["executed"] is False for x in suggestions(r))
def test_bm25_retrieval_and_review_evidence():
 r=fixture_repo();hits=retrieve(r,"calculate total items",limit=3)
 assert hits and hits[0]["path"]=="src/core.py" and hits[0]["start_line"]==1
 file={"content":"value = eval(user_input)\n# TODO: replace\n","complexity":13}
 findings=review_file("src/risky.py",file)
 assert any(x["severity"]=="high" and x["line"]==1 for x in findings)
 assert any("TODO" in x["message"] for x in findings)
def test_risk_model_gracefully_uses_transparent_baseline_without_history():
 result=risk_report(fixture_repo(),[])
 assert result["history_commits"]==0
 assert result["model"]["trained"] is False
 assert result["items"][0]["score_type"]=="transparent heuristic"

from app.services.intelligence import review_patch
def test_patch_review_uses_new_file_line_numbers():
 patch="@@ -10,1 +10,2 @@\n+value = eval(raw)\n+ # TODO\n"
 findings=review_patch("src/a.py",patch)
 assert any(x["line"]==10 and x["severity"]=="high" for x in findings)
 assert any(x["line"]==11 and "TODO" in x["message"] for x in findings)

def test_history_risk_model_uses_purged_time_split_and_baseline():
 repo=fixture_repo();history=[]
 for i in range(40):
  path=list(repo["files"])[i%3]
  bug=i%5==0
  history.append({"bug_fix_heuristic":bug,"files":[{"path":path,"additions":i%4,"deletions":i%2}]})
 result=risk_report(repo,history);model=result["model"]
 assert model["trained"] is True
 assert model["train_test_split"].startswith("time ordered")
 assert model["purge_gap_commits"]==4
 assert "churn_baseline" in model and "pr_auc" in model
 assert all(x["score_type"].startswith("relative model") for x in result["items"])

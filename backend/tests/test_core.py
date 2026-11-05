from app.core.security import parse_github_url,InvalidRepositoryURL
from app.engines.analysis.filtering import eligible
from app.engines.parser.analyzer import analyze_source

def test_urls():
 assert parse_github_url("https://github.com/pallets/flask")==("pallets","flask")
 assert parse_github_url("github.com/pallets/flask.git")==("pallets","flask")
 for v in ("http://github.com/a/b","https://example.com/a/b","https://github.com/a/b/issues"):
  try:parse_github_url(v)
  except InvalidRepositoryURL:pass
  else:assert False,v
def test_filtering():
 assert eligible("src/main.py",100,500)
 assert not eligible("node_modules/x.js",10,500)
 assert not eligible(".env",10,500)
 assert not eligible("src/huge.py",501,500)
def test_python_analysis():
 r=analyze_source("app.py","import os\nfrom pathlib import Path\ndef run(x):\n    if x and os.path.exists(x):\n        return Path(x)\n")
 assert r["symbols"][0]["name"]=="run"
 assert "os" in r["imports"] and "pathlib" in r["imports"]
 assert r["complexity"]>=3

from app.services.analysis import resolve_import
def test_import_resolution():
 paths={"src/app/main.py","src/app/services/store.py","src/app/util.js","src/app/index.js"}
 assert resolve_import("src/app/main.py","./services/store",paths)=="src/app/services/store.py"
 assert resolve_import("src/app/main.py","app.services.store",paths)=="src/app/services/store.py"
 assert resolve_import("src/app/util.js","./index",paths)=="src/app/index.js"
 assert resolve_import("src/app/main.py","external_library",paths) is None

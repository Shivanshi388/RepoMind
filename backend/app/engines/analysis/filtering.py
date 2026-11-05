import fnmatch
from pathlib import PurePosixPath
ALLOWED={".py",".pyi",".js",".jsx",".mjs",".cjs",".ts",".tsx",".java",".go",".rs",".rb",".php",".cs",".cpp",".cc",".c",".h",".hpp",".swift",".kt",".kts",".scala",".vue",".svelte",".html",".css",".scss",".json",".yaml",".yml",".toml",".md",".sql",".sh"}
SKIP_PARTS={"node_modules","vendor","dist","build","coverage",".git",".next","target","__pycache__",".venv","venv","out","bin","obj"}
def eligible(path:str,size:int,max_bytes:int)->bool:
 p=PurePosixPath(path);parts={x.lower() for x in p.parts};name=p.name.lower();low=path.lower()
 if not path or path.startswith("/") or "\\" in path or ".." in p.parts:return False
 if size<0 or size>max_bytes or p.suffix.lower() not in ALLOWED:return False
 if parts&SKIP_PARTS:return False
 if name in {".env",".env.local",".env.production","id_rsa","id_ed25519","credentials","credentials.json","secrets.json","secrets.yaml","secrets.yml"}:return False
 if name.startswith(".env.") or "secret" in name or "credential" in name:return False
 if any(x in low for x in (".min.","/generated/","/vendor/")):return False
 return not any(fnmatch.fnmatch(name,pat) for pat in ("*.map","*.lock","*.snap","*.sum"))

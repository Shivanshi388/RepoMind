import httpx
from app.core.config import settings
API="https://api.github.com"
class GitHubError(Exception):
 def __init__(self,message,status=502): self.message,self.status=message,status
class GitHubClient:
 def __init__(self):
  h={"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28","User-Agent":"RepoMind/1.0"}
  if settings.github_token:h["Authorization"]=f"Bearer {settings.github_token}"
  self.client=httpx.Client(base_url=API,headers=h,timeout=30,follow_redirects=False)
 def get(self,path):
  try:r=self.client.get(path)
  except httpx.HTTPError as e:raise GitHubError("GitHub could not be reached. Check your connection and try again.") from e
  if r.status_code==404:raise GitHubError("Repository not found, or it is not public.",404)
  if r.status_code==403 and r.headers.get("X-RateLimit-Remaining")=="0":raise GitHubError("GitHub rate limit reached. Try later or configure a public-repository token.",429)
  if r.status_code>=400:raise GitHubError(f"GitHub returned an error ({r.status_code}).",r.status_code)
  return r.json()
 def repository(self,owner,repo):return self.get(f"/repos/{owner}/{repo}")
 def tree(self,owner,repo,sha):return self.get(f"/repos/{owner}/{repo}/git/trees/{sha}?recursive=1")
 def archive(self,owner,repo,sha,limit):
  # Follow GitHub's documented archive redirect host and enforce a byte cap while streaming.
  url=f"{API}/repos/{owner}/{repo}/zipball/{sha}"
  try:
   r=self.client.get(url,follow_redirects=False)
   if r.status_code in (301,302,307,308):
    from urllib.parse import urljoin,urlparse
    target=urljoin(url,r.headers.get("location",""));parsed=urlparse(target)
    if parsed.scheme!="https" or parsed.hostname not in {"codeload.github.com","github.com"} or parsed.port not in (None,443) or parsed.username or parsed.password:
     raise GitHubError("GitHub returned an unexpected archive host.",502)
    chunks=[];total=0
    with httpx.stream("GET",target,headers={"User-Agent":"RepoMind/1.0"},timeout=60,follow_redirects=False) as stream:
     stream.raise_for_status()
     for chunk in stream.iter_bytes():
      total+=len(chunk)
      if total>limit:raise GitHubError("Repository archive exceeds the configured size limit.",413)
      chunks.append(chunk)
    return b"".join(chunks)
   r.raise_for_status()
   if len(r.content)>limit:raise GitHubError("Repository archive exceeds the configured size limit.",413)
   return r.content
  except GitHubError:raise
  except httpx.HTTPStatusError as e:raise GitHubError("Could not download the repository archive.",e.response.status_code) from e
  except httpx.HTTPError as e:raise GitHubError("Could not download the repository archive.") from e
 def close(self):self.client.close()

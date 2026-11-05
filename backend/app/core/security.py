import re
from urllib.parse import urlparse

class InvalidRepositoryURL(ValueError): pass

def parse_github_url(value: str) -> tuple[str, str]:
    """Accept only the canonical public github.com owner/repository URL."""
    value = value.strip()
    parsed = urlparse(value if "://" in value else "https://" + value)
    if parsed.scheme != "https" or parsed.hostname not in {"github.com", "www.github.com"}:
        raise InvalidRepositoryURL("Enter an HTTPS URL from github.com.")
    pieces = [p for p in parsed.path.split("/") if p]
    if len(pieces) != 2 or any(p in {".", ".."} for p in pieces):
        raise InvalidRepositoryURL("Use a repository URL in the form https://github.com/owner/repository.")
    owner, repo = pieces
    repo = re.sub(r"\.git$", "", repo)
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", owner) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", repo):
        raise InvalidRepositoryURL("The owner or repository name contains unsupported characters.")
    return owner, repo

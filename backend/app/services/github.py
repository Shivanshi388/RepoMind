import email.utils
import threading
import time
from collections import OrderedDict
from datetime import datetime, timezone

import httpx
from app.core.config import settings

API = "https://api.github.com"

_CACHE_TTL_SECONDS = 600
_CACHE_MAX_ENTRIES = 128
_CACHE_MAX_ENTRY_BYTES = 2 * 1024 * 1024
_CACHE_MAX_BYTES = 16 * 1024 * 1024
_GET_CACHE = OrderedDict()
_GET_CACHE_BYTES = 0
_CACHE_LOCK = threading.Lock()
_RATE_LIMIT_UNTIL = 0.0
_RATE_LIMIT_LOCK = threading.Lock()


class GitHubError(Exception):
    def __init__(self, message, status=502):
        self.message = message
        self.status = status


def _cached_get(key):
    now = time.monotonic()
    with _CACHE_LOCK:
        item = _GET_CACHE.get(key)
        if item is None:
            return None

        expires_at, payload, size = item
        if expires_at <= now:
            _GET_CACHE.pop(key, None)
            global _GET_CACHE_BYTES
            _GET_CACHE_BYTES -= size
            return None

        _GET_CACHE.move_to_end(key)
        return payload


def _cache_get(key, payload, size):
    global _GET_CACHE_BYTES
    if size > _CACHE_MAX_ENTRY_BYTES:
        return

    with _CACHE_LOCK:
        previous = _GET_CACHE.pop(key, None)
        if previous is not None:
            _GET_CACHE_BYTES -= previous[2]

        _GET_CACHE[key] = (time.monotonic() + _CACHE_TTL_SECONDS, payload, size)
        _GET_CACHE_BYTES += size

        while (
            len(_GET_CACHE) > _CACHE_MAX_ENTRIES
            or _GET_CACHE_BYTES > _CACHE_MAX_BYTES
        ):
            _, (_, _, removed_size) = _GET_CACHE.popitem(last=False)
            _GET_CACHE_BYTES -= removed_size


def _retry_after_seconds(response):
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        try:
            return max(1, int(float(retry_after)))
        except ValueError:
            try:
                retry_time = email.utils.parsedate_to_datetime(retry_after)
                if retry_time.tzinfo is None:
                    retry_time = retry_time.replace(tzinfo=timezone.utc)
                return max(
                    1,
                    int((retry_time - datetime.now(timezone.utc)).total_seconds()),
                )
            except (TypeError, ValueError, OverflowError):
                pass

    reset_at = response.headers.get("X-RateLimit-Reset")
    if reset_at:
        try:
            return max(1, int(float(reset_at) - time.time()))
        except (TypeError, ValueError, OverflowError):
            pass

    return 60


def _raise_if_rate_limited(response):
    if response.status_code not in (403, 429):
        return

    body = response.text.lower()
    exhausted = response.headers.get("X-RateLimit-Remaining") == "0"
    rate_limit_message = "rate limit" in body or "secondary rate" in body

    if response.status_code == 429 or exhausted or rate_limit_message:
        wait_seconds = _retry_after_seconds(response)
        if wait_seconds >= 60:
            wait_text = f"about {(wait_seconds + 59) // 60} minutes"
        else:
            wait_text = f"{wait_seconds} seconds"

        global _RATE_LIMIT_UNTIL
        with _RATE_LIMIT_LOCK:
            _RATE_LIMIT_UNTIL = max(
                _RATE_LIMIT_UNTIL,
                time.time() + wait_seconds,
            )
        raise GitHubError(
            f"GitHub's API rate limit was reached. Try again in {wait_text}.",
            429,
        )


def _check_rate_limit_cooldown():
    with _RATE_LIMIT_LOCK:
        remaining = _RATE_LIMIT_UNTIL - time.time()
    if remaining > 0:
        wait_seconds = max(1, int(remaining + 0.999))
        if wait_seconds >= 60:
            wait_text = f"about {(wait_seconds + 59) // 60} minutes"
        else:
            wait_text = f"{wait_seconds} seconds"
        raise GitHubError(
            f"GitHub's API rate limit was reached. Try again in {wait_text}.",
            429,
        )


class GitHubClient:
    def __init__(self):
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "RepoMind/1.0",
        }
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"

        self.client = httpx.Client(
            base_url=API,
            headers=headers,
            timeout=30,
            follow_redirects=False,
        )

    def get(self, path):
        cached = _cached_get(path)
        if cached is not None:
            return cached

        _check_rate_limit_cooldown()
        try:
            response = self.client.get(path)
        except httpx.HTTPError as exc:
            raise GitHubError(
                "GitHub could not be reached. Check your connection and try again."
            ) from exc

        if response.status_code == 404:
            raise GitHubError("Repository not found, or it is not public.", 404)

        _raise_if_rate_limited(response)

        if response.status_code >= 400:
            raise GitHubError(
                f"GitHub returned an error ({response.status_code}).",
                response.status_code,
            )

        payload = response.json()
        _cache_get(path, payload, len(response.content))
        return payload

    def repository(self, owner, repo):
        return self.get(f"/repos/{owner}/{repo}")

    def tree(self, owner, repo, sha):
        return self.get(f"/repos/{owner}/{repo}/git/trees/{sha}?recursive=1")

    def archive(self, owner, repo, sha, limit):
        url = f"{API}/repos/{owner}/{repo}/zipball/{sha}"
        _check_rate_limit_cooldown()
        try:
            response = self.client.get(url, follow_redirects=False)
            _raise_if_rate_limited(response)

            if response.status_code in (301, 302, 307, 308):
                from urllib.parse import urljoin, urlparse

                target = urljoin(url, response.headers.get("location", ""))
                parsed = urlparse(target)
                if (
                    parsed.scheme != "https"
                    or parsed.hostname not in {"codeload.github.com", "github.com"}
                    or parsed.port not in (None, 443)
                    or parsed.username
                    or parsed.password
                ):
                    raise GitHubError("GitHub returned an unexpected archive host.", 502)

                chunks = []
                total = 0
                with httpx.stream(
                    "GET",
                    target,
                    headers={"User-Agent": "RepoMind/1.0"},
                    timeout=60,
                    follow_redirects=False,
                ) as stream:
                    stream.raise_for_status()
                    for chunk in stream.iter_bytes():
                        total += len(chunk)
                        if total > limit:
                            raise GitHubError(
                                "Repository archive exceeds the configured size limit.",
                                413,
                            )
                        chunks.append(chunk)

                return b"".join(chunks)

            response.raise_for_status()
            if len(response.content) > limit:
                raise GitHubError(
                    "Repository archive exceeds the configured size limit.",
                    413,
                )
            return response.content

        except GitHubError:
            raise
        except httpx.HTTPStatusError as exc:
            raise GitHubError(
                "Could not download the repository archive.",
                exc.response.status_code,
            ) from exc
        except httpx.HTTPError as exc:
            raise GitHubError("Could not download the repository archive.") from exc

    def close(self):
        self.client.close()
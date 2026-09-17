from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request


def request_json(
    url: str, *, headers=None, method="GET", payload=None, no_proxy=False,
    timeout=20, retries=0,
):
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request_headers = {"Accept": "application/json", **(headers or {})}
    if body is not None:
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=request_headers, method=method)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({})) if no_proxy else urllib.request.build_opener()
    for attempt in range(retries + 1):
        try:
            with opener.open(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8")), dict(response.headers)
        except (urllib.error.URLError, TimeoutError):
            if attempt == retries:
                raise
            time.sleep(2 ** attempt)


def request_text(url: str, *, headers=None, no_proxy=False):
    request = urllib.request.Request(url, headers=headers or {})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({})) if no_proxy else urllib.request.build_opener()
    with opener.open(request, timeout=20) as response:
        return response.read().decode("utf-8").strip()


def query_url(base: str, params: dict) -> str:
    return f"{base}?{urllib.parse.urlencode(params)}"

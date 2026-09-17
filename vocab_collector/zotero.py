from __future__ import annotations

import urllib.error
from urllib.parse import unquote, urlparse

from .http import query_url, request_json, request_text


class ZoteroError(RuntimeError):
    pass


class ZoteroClient:
    base_url = "http://127.0.0.1:23119/api"

    def _json(self, path: str, params=None):
        url = self.base_url + path
        if params:
            url = query_url(url, params)
        try:
            return request_json(url, headers={"Zotero-API-Version": "3"}, no_proxy=True)[0]
        except urllib.error.HTTPError as exc:
            if exc.code == 403:
                raise ZoteroError(
                    "本地 API 未开启。请在 Zotero 设置 → 高级中勾选“允许本机其他应用与 Zotero 通信”。"
                ) from exc
            raise ZoteroError(f"Zotero Local API 返回 HTTP {exc.code}") from exc
        except OSError as exc:
            raise ZoteroError("无法连接 Zotero，请确认 Zotero 桌面端正在运行。") from exc

    def status(self):
        try:
            _, headers = request_json(
                self.base_url + "/users/0/items?limit=1",
                headers={"Zotero-API-Version": "3"},
                no_proxy=True,
            )
            return {"version": headers.get("X-Zotero-Version", "未知")}
        except urllib.error.HTTPError as exc:
            if exc.code == 403:
                version = exc.headers.get("X-Zotero-Version", "未知")
                raise ZoteroError(f"检测到 Zotero {version}，但本地 API 未开启") from exc
            raise ZoteroError(f"Zotero Local API 返回 HTTP {exc.code}") from exc
        except OSError as exc:
            raise ZoteroError("未检测到运行中的 Zotero。") from exc

    def annotations(self):
        annotations = []
        start = 0
        limit = 50
        while True:
            batch = self._json(
                "/users/0/items",
                {
                    "itemType": "annotation",
                    "format": "json",
                    "include": "data",
                    "limit": limit,
                    "start": start,
                },
            )
            annotations.extend(batch)
            if len(batch) < limit:
                return annotations
            start += len(batch)

    def collections(self):
        return self._json("/users/0/collections", {"format": "json", "include": "data"})

    def papers(self, collection_key: str | None = None):
        path = "/users/0/items/top" if collection_key is None else f"/users/0/collections/{collection_key}/items/top"
        items = self._json(path, {"format": "json", "include": "data"})
        excluded = {"attachment", "note", "annotation"}
        return [item for item in items if item.get("data", item).get("itemType") not in excluded]

    def item(self, key: str):
        return self._json(f"/users/0/items/{key}")

    def attachment_path(self, key: str):
        url = f"{self.base_url}/users/0/items/{key}/file/view/url"
        try:
            value = request_text(url, headers={"Zotero-API-Version": "3"}, no_proxy=True)
        except (urllib.error.HTTPError, OSError):
            return None
        parsed = urlparse(value)
        if parsed.scheme != "file":
            return None
        path = unquote(parsed.path)
        if parsed.netloc:
            path = f"//{parsed.netloc}{path}"
        if len(path) >= 3 and path[0] == "/" and path[2] == ":":
            path = path[1:]
        return path

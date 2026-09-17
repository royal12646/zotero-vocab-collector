from __future__ import annotations

import json
import html
import re
import urllib.error
from dataclasses import replace
from pathlib import Path

from .http import query_url, request_json


WORD = re.compile(r"^[A-Za-z]+(?:[-'][A-Za-z]+)*$")


class Enricher:
    def __init__(self, email: str, cache_path: Path):
        self.email = email
        self.cache_path = cache_path
        self.cache = self._load_cache()

    def _load_cache(self):
        if not self.cache_path.exists():
            return {}
        try:
            return json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_cache(self):
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2), encoding="utf-8")

    def _translation_candidates(self, text: str) -> list[str]:
        params = {"q": text, "langpair": "en|zh-CN"}
        if self.email:
            params["de"] = self.email
        try:
            payload, _ = request_json(query_url("https://api.mymemory.translated.net/get", params))
            values = [payload.get("responseData", {}).get("translatedText", "")]
            if WORD.fullmatch(text):
                values.extend(match.get("translation", "") for match in payload.get("matches", [])[:10])
            candidates = []
            for value in values:
                translated = html.unescape(str(value)).strip().replace(" ,", "，").replace(", ", "、")
                if translated and translated.casefold() != text.casefold() and translated not in candidates:
                    candidates.append(translated)
            return candidates[:5]
        except (urllib.error.HTTPError, OSError, ValueError):
            return []

    def _rich_translation(self, term: str) -> str:
        candidates = self._translation_candidates(term)
        lines = []
        if candidates:
            lines.append(f"常用义：{candidates[0]}")
            if len(candidates) > 1:
                lines.append("其他释义：" + "；".join(candidates[1:]))
        return "\n".join(lines)

    def enrich(self, row):
        key = "v5|" + row.term.casefold()
        value = self.cache.get(key)
        if value is None:
            value = {
                "translation": self._rich_translation(row.term),
                "pronunciation": "",
                "audio_url": "",
            }
            self.cache[key] = value
            self._save_cache()
        return replace(row, **value)

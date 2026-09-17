from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VocabularyRow:
    term: str
    sentence: str
    paper: str
    page: str
    zotero_url: str
    annotation_key: str
    context_status: str = "ok"
    translation: str = ""
    pronunciation: str = ""
    audio_url: str = ""


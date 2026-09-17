from __future__ import annotations

import json
import re
from pathlib import Path


ABBREVIATIONS = {"e.g.", "i.e.", "et al.", "fig.", "eq.", "ref.", "dr.", "mr.", "vs."}


def page_index(position) -> int | None:
    if isinstance(position, str):
        try:
            position = json.loads(position)
        except json.JSONDecodeError:
            return None
    if not isinstance(position, dict):
        return None
    value = position.get("pageIndex")
    return value if isinstance(value, int) and value >= 0 else None


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u00ad", "").replace("-\n", "")).strip()


def _is_boundary(text: str, index: int) -> bool:
    if text[index] not in ".?!":
        return False
    prefix = text[max(0, index - 8) : index + 1].lower()
    if any(prefix.endswith(abbr) for abbr in ABBREVIATIONS):
        return False
    if 0 < index < len(text) - 1 and text[index - 1].isdigit() and text[index + 1].isdigit():
        return False
    return index + 1 == len(text) or text[index + 1].isspace()


def containing_sentence(text: str, term: str) -> tuple[str, str]:
    clean_text = normalize(text)
    clean_term = normalize(term)
    if not clean_term:
        return "", "missing-term"
    pattern = re.compile(re.escape(clean_term), re.IGNORECASE)
    matches = list(pattern.finditer(clean_text))
    if not matches:
        flexible = re.compile(r"\s+".join(re.escape(part) for part in clean_term.split()), re.IGNORECASE)
        matches = list(flexible.finditer(clean_text))
    if not matches:
        return clean_term, "term-not-found-on-page"
    match = matches[0]
    start = 0
    for index in range(match.start() - 1, -1, -1):
        if _is_boundary(clean_text, index):
            start = index + 1
            break
    end = len(clean_text)
    for index in range(match.end(), len(clean_text)):
        if _is_boundary(clean_text, index):
            end = index + 1
            break
    status = "ok" if len(matches) == 1 else "multiple-matches-first-used"
    return clean_text[start:end].strip(), status


def sentence_from_pdf(path: str | None, index: int | None, term: str) -> tuple[str, str]:
    if not path or index is None:
        return term, "pdf-or-page-unavailable"
    try:
        import pymupdf
        with pymupdf.open(Path(path)) as document:
            if index >= document.page_count:
                return term, "page-out-of-range"
            text = document.load_page(index).get_text("text")
    except (ImportError, OSError, ValueError, RuntimeError):
        return term, "pdf-text-unavailable"
    if not text.strip():
        return term, "ocr-required"
    return containing_sentence(text, term)

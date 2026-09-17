from __future__ import annotations

from .context import page_index, sentence_from_pdf
from .models import VocabularyRow


class Collector:
    def __init__(self, zotero, highlight_color: str):
        self.zotero = zotero
        self.highlight_color = highlight_color.lower()
        self._items = {}

    def _item(self, key: str):
        if key not in self._items:
            self._items[key] = self.zotero.item(key)
        return self._items[key]

    def collect(self, selected_paper_key: str | None = None):
        rows = []
        seen = set()
        for raw in self.zotero.annotations():
            data = raw.get("data", raw)
            if data.get("annotationType") != "highlight":
                continue
            if data.get("annotationColor", "").lower() != self.highlight_color:
                continue
            term = (data.get("annotationText") or "").strip()
            annotation_key = data.get("key") or raw.get("key", "")
            if not term or not annotation_key or annotation_key in seen:
                continue
            seen.add(annotation_key)
            attachment_key = data.get("parentItem", "")
            attachment = self._item(attachment_key).get("data", {}) if attachment_key else {}
            resolved_paper_key = attachment.get("parentItem", "")
            if selected_paper_key is not None and resolved_paper_key != selected_paper_key:
                continue
            paper = self._item(resolved_paper_key).get("data", {}) if resolved_paper_key else attachment
            page = str(data.get("annotationPageLabel") or "")
            sentence, status = sentence_from_pdf(
                self.zotero.attachment_path(attachment_key),
                page_index(data.get("annotationPosition")),
                term,
            )
            link = f"zotero://open-pdf/library/items/{attachment_key}?annotation={annotation_key}"
            rows.append(VocabularyRow(
                term=term,
                sentence=sentence,
                paper=paper.get("title") or attachment.get("title") or "未命名论文",
                page=page,
                zotero_url=link,
                annotation_key=annotation_key,
                context_status=status,
            ))
        return rows

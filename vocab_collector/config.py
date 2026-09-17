from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


@dataclass(frozen=True)
class Config:
    highlight_color: str
    mymemory_email: str

    @classmethod
    def from_environment(cls) -> "Config":
        return cls(
            highlight_color=os.getenv("ZOTERO_HIGHLIGHT_COLOR", "#2ea8e5").lower(),
            mymemory_email=os.getenv("MYMEMORY_EMAIL", ""),
        )

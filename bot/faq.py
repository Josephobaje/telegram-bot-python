"""Keyword-based FAQ matcher. Edit ``faq.json`` to customise the answers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

_WORD_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class FaqEntry:
    question: str
    answer: str
    keywords: tuple[str, ...]


def load_faq(path: Path) -> list[FaqEntry]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [FaqEntry(e["question"], e["answer"], tuple(k.lower() for k in e["keywords"])) for e in data]


def best_answer(text: str, entries: list[FaqEntry], min_hits: int = 1) -> FaqEntry | None:
    """Return the entry whose keywords overlap most with ``text``."""
    words = set(_WORD_RE.findall(text.lower()))
    best, best_hits = None, 0
    for entry in entries:
        hits = sum(1 for k in entry.keywords if (k in words if " " not in k else k in text.lower()))
        if hits > best_hits:
            best, best_hits = entry, hits
    return best if best_hits >= min_hits else None

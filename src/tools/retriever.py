from __future__ import annotations

import os
from typing import List, Tuple

_KB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge")


def _load_kb_docs() -> List[Tuple[str, str]]:
    docs: List[Tuple[str, str]] = []
    if not os.path.isdir(_KB_DIR):
        return docs
    for name in os.listdir(_KB_DIR):
        if not name.endswith(".md"):
            continue
        path = os.path.join(_KB_DIR, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                docs.append((name, f.read()))
        except Exception:
            pass
    return docs


class KnowledgeBase:
    def __init__(self) -> None:
        self.docs = _load_kb_docs()

    def retrieve(self, hints: List[str], top_k: int = 3) -> List[str]:
        if not hints or not self.docs:
            return []
        scored: List[Tuple[int, str]] = []
        for name, content in self.docs:
            score = sum(content.count(h) for h in hints)
            if score:
                scored.append((score, f"{name}:\n{content}"))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]] 
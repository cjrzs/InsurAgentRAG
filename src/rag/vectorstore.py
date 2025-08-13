from __future__ import annotations

import os
from typing import List, Tuple

import faiss  # type: ignore
from sentence_transformers import SentenceTransformer
import numpy as np

from ..config import rag_config
import asyncio


class VectorStore:
    def __init__(self) -> None:
        self.embedder = SentenceTransformer(rag_config.embedding_model)
        self.index: faiss.IndexFlatIP | None = None
        self.docs: List[Tuple[str, str]] = []  # (doc_id, text)
        self._load_index()

    def _load_index(self) -> None:
        if os.path.isfile(rag_config.index_path) and os.path.isfile(rag_config.index_path + ".meta"):
            self.index = faiss.read_index(rag_config.index_path)
            with open(rag_config.index_path + ".meta", "r", encoding="utf-8") as f:
                for line in f:
                    doc_id, text = line.rstrip("\n").split("\t", 1)
                    self.docs.append((doc_id, text))
        else:
            self.build_from_dir(rag_config.knowledge_dir)

    def build_from_dir(self, dir_path: str) -> None:
        contents: List[Tuple[str, str]] = []
        if os.path.isdir(dir_path):
            for name in os.listdir(dir_path):
                if name.endswith(".md") or name.endswith(".txt"):
                    p = os.path.join(dir_path, name)
                    with open(p, "r", encoding="utf-8") as f:
                        text = f.read()
                        contents.append((name, text))
        if not contents:
            # seed with an empty index to avoid crash
            self.index = faiss.IndexFlatIP(384)
            self.docs = []
            return
        embeddings = self.embedder.encode([c[1] for c in contents], normalize_embeddings=True)
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings.astype(np.float32))
        self.docs = contents
        faiss.write_index(self.index, rag_config.index_path)
        with open(rag_config.index_path + ".meta", "w", encoding="utf-8") as f:
            for doc_id, text in self.docs:
                f.write(f"{doc_id}\t{text}\n")

    def search(self, queries: List[str], top_k: int | None = None) -> List[str]:
        if self.index is None or not self.docs or not queries:
            return []
        top_k = top_k or rag_config.top_k
        q_emb = self.embedder.encode(queries, normalize_embeddings=True).astype(np.float32)
        sims, idxs = self.index.search(q_emb, top_k)
        seen = set()
        results: List[str] = []
        for row in idxs:
            for i in row:
                if i < 0 or i >= len(self.docs):
                    continue
                if i in seen:
                    continue
                seen.add(i)
                results.append(self.docs[i][1])
        return results

    async def abuild_from_dir(self, dir_path: str) -> None:
        await asyncio.to_thread(self.build_from_dir, dir_path)

    async def asearch(self, queries: List[str], top_k: int | None = None) -> List[str]:
        return await asyncio.to_thread(self.search, queries, top_k) 

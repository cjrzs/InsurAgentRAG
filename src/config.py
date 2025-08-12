from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelConfig:
    # Windows paths as requested; can be overridden by env vars
    base_model_dir: str = os.getenv("LOCAL_QWEN_DIR", r"D:\LLM\Qwen3-4B")
    lora_adapter_dir: Optional[str] = os.getenv(
        "LORA_ADAPTER_DIR",
        r"D:\PycharmProjects\LoveYiNuo\RAG\model-sft\output\v4-20250805-171721\checkpoint-500",
    )
    max_new_tokens: int = int(os.getenv("MAX_NEW_TOKENS", "1024"))
    temperature: float = float(os.getenv("GEN_TEMPERATURE", "0.2"))


@dataclass
class DBConfig:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./insur_agent.db")


@dataclass
class RagConfig:
    knowledge_dir: str = os.getenv("KNOWLEDGE_DIR", os.path.join(os.path.dirname(__file__), "knowledge"))
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
    index_path: str = os.getenv("FAISS_INDEX_PATH", os.path.join(os.path.dirname(__file__), "rag_index.faiss"))
    top_k: int = int(os.getenv("RAG_TOP_K", "4"))


model_config = ModelConfig()
rag_config = RagConfig()
_db_config = DBConfig()

def get_database_url() -> str:
    return _db_config.database_url 
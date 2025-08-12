from __future__ import annotations

import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..db.models import fetch_user_request
from ..graph.pipeline_graph import PipelineGraph


class GenerateRequest(BaseModel):
    user_id: int


app = FastAPI(title="InsurAgentRAG API", version="0.1.0")


@app.post("/strategy/generate")
def generate_strategy(body: GenerateRequest):
    req = fetch_user_request(body.user_id)
    if not req:
        raise HTTPException(status_code=404, detail="User not found")

    graph = PipelineGraph().build()
    state = {"req": req}
    out = graph.invoke(state)
    final_json = out.get("final_json")
    try:
        data = json.loads(final_json)
    except Exception:
        # 若 LLM 格式不完全，直接返回原文本，便于前端观察与调试
        return {"raw": final_json}
    return data 
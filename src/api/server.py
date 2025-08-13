from __future__ import annotations

import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..db.models import afetch_user_request
from ..graph.pipeline_graph import PipelineGraph
import asyncio


class GenerateRequest(BaseModel):
    user_id: int


app = FastAPI(title="InsurAgentRAG API", version="0.1.0")


@app.post("/strategy/generate")
async def generate_strategy(body: GenerateRequest):
    req = await afetch_user_request(body.user_id)
    if not req:
        raise HTTPException(status_code=404, detail="User not found")

    out = await PipelineGraph().arun(req)
    final_json = out.get("final_json")
    try:
        data = json.loads(final_json)
    except Exception:
        # 若 LLM 格式不完全，直接返回原文本，便于前端观察与调试
        return {"raw": final_json}
    return data 
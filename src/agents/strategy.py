from __future__ import annotations

from typing import List

from .base_agent import BaseAgent
from ..models.schemas import UserRequest, StrategyRecommendation
from ..tools.llm import StrategyGenerator
import asyncio


class StrategyAgent(BaseAgent):
    def __init__(self, name, llm, tools=None, memory=None):
        super().__init__(name, llm, tools, memory)
        self.generator = StrategyGenerator(llm)

    def act(self, req: UserRequest, context_docs: List[str]) -> StrategyRecommendation:  # type: ignore[override]
        return self.generator.generate(req, context_docs)

    async def aact(self, req: UserRequest, context_docs: List[str]) -> StrategyRecommendation:  # type: ignore[override]
        return await self.generator.agenerate(req, context_docs) 
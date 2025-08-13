from __future__ import annotations

from .base_agent import BaseAgent
from ..models.schemas import UserRequest, StrategyRecommendation, RiskWarning
from ..tools.evaluator import assess_budget, assess_gaps
import asyncio


class RiskAgent(BaseAgent):
    def act(self, req: UserRequest, rec: StrategyRecommendation) -> StrategyRecommendation:  # type: ignore[override]
        warnings: list[RiskWarning] = []
        warnings.extend(rec.risk_warnings)
        warnings.extend(assess_budget(req, rec))
        warnings.extend(assess_gaps(req, rec))
        # 去重（按segment+advice）
        uniq: dict[tuple[str, str], RiskWarning] = {}
        for w in warnings:
            uniq[(w.segment, w.advice)] = w
        rec.risk_warnings = list(uniq.values())
        return rec

    async def aact(self, req: UserRequest, rec: StrategyRecommendation) -> StrategyRecommendation:  # type: ignore[override]
        return await asyncio.to_thread(self.act, req, rec) 
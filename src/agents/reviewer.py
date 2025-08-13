from __future__ import annotations

from typing import List

from .base_agent import BaseAgent
from ..models.schemas import StrategyRecommendation
from ..tools.evaluator import build_renewal_claims_tips
import asyncio


class ReviewAgent(BaseAgent):
    def act(self, rec: StrategyRecommendation) -> StrategyRecommendation:  # type: ignore[override]
        # 填充续保/理赔提醒
        if not rec.renewal_and_claims.get("renewal") or not rec.renewal_and_claims.get("claims"):
            renewal, claims = build_renewal_claims_tips()
            rec.renewal_and_claims = {"renewal": renewal, "claims": claims}

        # 简单完整性检查
        assert rec.items, "策略项不能为空"
        assert rec.purchase_plan, "需包含分阶段购买计划"
        assert rec.policy_combo_explanation, "需包含保单组合说明"
        return rec

    async def aact(self, rec: StrategyRecommendation) -> StrategyRecommendation:  # type: ignore[override]
        return await asyncio.to_thread(self.act, rec) 
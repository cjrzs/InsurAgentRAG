from __future__ import annotations

from typing import List

from .base_agent import BaseAgent
from ..models.schemas import StrategyRecommendation, PurchaseStep
import asyncio


class ExecutionAgent(BaseAgent):
    def act(self, rec: StrategyRecommendation) -> StrategyRecommendation:  # type: ignore[override]
        # 在已有 purchase_plan 基础上，微调动作描述
        refined: List[PurchaseStep] = []
        for step in rec.purchase_plan:
            actions = list(step.actions)
            if step.phase == "now":
                actions.append("确认核保材料（体检、问卷、既往病史证明）")
            if step.phase == "6m":
                actions.append("回顾现金流与保费承受度")
            if step.phase == "12m":
                actions.append("评估家庭结构变化（结婚/生育/赡养）")
            refined.append(PurchaseStep(phase=step.phase, actions=actions))

        rec.purchase_plan = refined
        return rec

    async def aact(self, rec: StrategyRecommendation) -> StrategyRecommendation:  # type: ignore[override]
        return await asyncio.to_thread(self.act, rec) 
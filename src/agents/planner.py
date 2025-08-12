from __future__ import annotations

from .base_agent import BaseAgent
from ..models.schemas import UserRequest


class PlannerAgent(BaseAgent):
    def act(self, req: UserRequest):  # type: ignore[override]
        # 输出结构化的全局计划（由执行与风控等 Agent 逐步完成）
        return {
            "steps": [
                {"id": "retrieve_kb", "desc": "检索相关知识库，组装上下文"},
                {"id": "draft_strategy", "desc": "调用LLM/启发式生成结构化策略草案"},
                {"id": "execution_plan", "desc": "细化分阶段购买与保单互补说明"},
                {"id": "risk_check", "desc": "预算与缺口检查，输出风险提示"},
                {"id": "review", "desc": "复核完整性，输出最终建议"},
            ]
        }


# 保留旧名，避免外部引用出错；新的策略生成放到 agents/strategy.py
class StrategyAgent(BaseAgent):
    def act(self, insured_info, current_policies):  # type: ignore[override]
        prompt = f"受保人信息：{insured_info}\n当前保单：{current_policies}"
        return self.llm.generate_text("你是资深保险顾问", prompt)


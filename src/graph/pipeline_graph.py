from __future__ import annotations

from typing import Dict, Any, List

try:
    from langgraph.graph import StateGraph, END  # type: ignore
except Exception:
    StateGraph = None  # type: ignore
    END = None  # type: ignore

from ..agents.prompts import PLANNER_SYSTEM, STRATEGY_SYSTEM, RISK_SYSTEM, REVIEW_SYSTEM
from ..tools.local_llm import LocalQwen
from ..rag.vectorstore import VectorStore
from ..models.schemas import UserRequest, StrategyRecommendation
import asyncio


class PipelineGraph:
    def __init__(self) -> None:
        self.llm = LocalQwen()
        self.vs = VectorStore()

    def build(self):
        if StateGraph is None:
            raise RuntimeError("LangGraph 未安装，请安装 langgraph 以使用图编排")

        def plan_node(state: Dict[str, Any]) -> Dict[str, Any]:
            req: UserRequest = state["req"]
            hints = list(set((req.knowledge_hints or []) + req.goals.goals))
            plan = {
                "steps": [
                    {"id": "rag", "desc": "向量检索相关知识"},
                    {"id": "strategy", "desc": "生成结构化策略"},
                    {"id": "risk", "desc": "风险合并与提示"},
                    {"id": "review", "desc": "复核与补全"},
                ]
            }
            return {**state, "plan": plan, "hints": hints}

        def rag_node(state: Dict[str, Any]) -> Dict[str, Any]:
            hints: List[str] = state.get("hints", [])
            ctx_docs = self.vs.search(hints, top_k=4)
            return {**state, "ctx_docs": ctx_docs}

        def strategy_node(state: Dict[str, Any]) -> Dict[str, Any]:
            req: UserRequest = state["req"]
            ctx = state.get("ctx_docs", [])
            user_prompt = (
                f"受保人信息: {req.insured.model_dump()}\n"
                f"财务状况: {req.finance.model_dump()}\n"
                f"保险目的: {req.goals.model_dump()}\n"
                f"已有保单: {[p.model_dump() for p in req.existing_policies]}\n"
                f"检索上下文(节选):\n{chr(10).join(ctx[:3])}\n"
                "请输出严格符合 schema 的 JSON。"
            )
            text = self.llm.chat(STRATEGY_SYSTEM, user_prompt)
            return {**state, "strategy_json": text}

        def risk_node(state: Dict[str, Any]) -> Dict[str, Any]:
            req: UserRequest = state["req"]
            # 将 req + strategy_json 一起给风控进行 JSON 合并（由前置 prompt 约束）
            user_prompt = (
                f"投保人: {req.insured.model_dump()}\n财务: {req.finance.model_dump()}\n目标: {req.goals.model_dump()}\n"
                f"策略草案(JSON):\n{state.get('strategy_json','')}\n"
                "仅输出风控合并后的 risk_warnings JSON 数组。"
            )
            text = self.llm.chat(RISK_SYSTEM, user_prompt)
            return {**state, "risk_json": text}

        def review_node(state: Dict[str, Any]) -> Dict[str, Any]:
            user_prompt = (
                f"策略草案(JSON):\n{state.get('strategy_json','')}\n"
                f"风控(JSON):\n{state.get('risk_json','')}\n"
                "请输出修订后的最终 JSON 对象。"
            )
            text = self.llm.chat(REVIEW_SYSTEM, user_prompt)
            return {**state, "final_json": text}

        graph = StateGraph(dict)
        graph.add_node("plan", plan_node)
        graph.add_node("rag", rag_node)
        graph.add_node("strategy", strategy_node)
        graph.add_node("risk", risk_node)
        graph.add_node("review", review_node)

        graph.set_entry_point("plan")
        graph.add_edge("plan", "rag")
        graph.add_edge("rag", "strategy")
        graph.add_edge("strategy", "risk")
        graph.add_edge("risk", "review")
        graph.add_edge("review", END)
        return graph.compile()

    async def arun(self, req: UserRequest) -> Dict[str, Any]:
        # 使用与同步图逻辑等价的异步实现，避免阻塞事件循环
        hints = list(set((req.knowledge_hints or []) + req.goals.goals))
        ctx_docs = await self.vs.asearch(hints, top_k=4)

        user_prompt_strategy = (
            f"受保人信息: {req.insured.model_dump()}\n"
            f"财务状况: {req.finance.model_dump()}\n"
            f"保险目的: {req.goals.model_dump()}\n"
            f"已有保单: {[p.model_dump() for p in req.existing_policies]}\n"
            f"检索上下文(节选):\n{chr(10).join(ctx_docs[:3])}\n"
            "请输出严格符合 schema 的 JSON。"
        )
        strategy_json = await self.llm.achat(STRATEGY_SYSTEM, user_prompt_strategy)

        user_prompt_risk = (
            f"投保人: {req.insured.model_dump()}\n财务: {req.finance.model_dump()}\n目标: {req.goals.model_dump()}\n"
            f"策略草案(JSON):\n{strategy_json}\n"
            "仅输出风控合并后的 risk_warnings JSON 数组。"
        )
        risk_json = await self.llm.achat(RISK_SYSTEM, user_prompt_risk)

        user_prompt_review = (
            f"策略草案(JSON):\n{strategy_json}\n"
            f"风控(JSON):\n{risk_json}\n"
            "请输出修订后的最终 JSON 对象。"
        )
        final_json = await self.llm.achat(REVIEW_SYSTEM, user_prompt_review)

        return {"final_json": final_json, "strategy_json": strategy_json, "risk_json": risk_json, "ctx_docs": ctx_docs} 
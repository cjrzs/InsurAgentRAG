from __future__ import annotations

import os
from typing import List, Optional

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore

from ..models.schemas import (
    UserRequest,
    StrategyRecommendation,
    StrategyItem,
    PurchaseStep,
    RiskWarning,
)
import asyncio


class LLMClient:
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.2) -> None:
        self.model = model
        self.temperature = temperature
        self._client = None
        if os.getenv("OPENAI_API_KEY") and OpenAI is not None:
            try:
                self._client = OpenAI()
            except Exception:
                self._client = None

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        if self._client is None:
            # Fallback dummy output for offline/demo runs
            return (
                "[MockLLM] 根据输入与知识上下文，已生成初步策略草案。"
            )
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return resp.choices[0].message.content or ""
        except Exception as e:  # pragma: no cover
            return f"[LLM Error] {e}"

    async def agenerate_text(self, system_prompt: str, user_prompt: str) -> str:
        # 若官方库无异步实现，退回线程池
        return await asyncio.to_thread(self.generate_text, system_prompt, user_prompt)


def _years_to_retirement(age: int, retire_age: int = 65) -> int:
    return max(10, retire_age - age)


def _default_beneficiary(family_structure: str) -> str:
    if any(k in family_structure for k in ["子", "女", "孩子", "child"]):
        return "配偶与子女按法定比例"
    return "配偶或父母按法定比例"


def _infer_items_by_goal(req: UserRequest) -> List[StrategyItem]:
    items: List[StrategyItem] = []
    years = _years_to_retirement(req.insured.age)
    beneficiary = _default_beneficiary(req.insured.family_structure)
    income = req.finance.annual_income

    goal_set = set(req.goals.goals)

    if "income_protection" in goal_set:
        recommended = max(5 * income, 300_000.0)
        items.append(
            StrategyItem(
                coverage_type="term_life",
                recommended_sum_assured=recommended,
                term_years=years,
                payment_mode="annual",
                beneficiary=beneficiary,
                rationale="以5-10年收入为参考，保障家庭收入中断风险"
            )
        )

    if "critical_illness" in goal_set:
        recommended = max(300_000.0, 0.5 * income)
        items.append(
            StrategyItem(
                coverage_type="critical_illness",
                recommended_sum_assured=recommended,
                term_years=years,
                payment_mode="annual",
                beneficiary=beneficiary,
                rationale="重疾治疗与康复费用准备，覆盖重大疾病带来的高额支出"
            )
        )

    if "medical_expense" in goal_set:
        items.append(
            StrategyItem(
                coverage_type="medical",
                recommended_sum_assured=2_000_000.0,
                term_years=1,
                payment_mode="annual",
                beneficiary=beneficiary,
                rationale="报销型医疗，含住院/手术/门诊急诊，优先选择高额医保外责任"
            )
        )

    if "accident" in goal_set:
        items.append(
            StrategyItem(
                coverage_type="accident",
                recommended_sum_assured=1_000_000.0,
                term_years=1,
                payment_mode="annual",
                beneficiary=beneficiary,
                rationale="意外身故/伤残及意外医疗保障，补足公共出行与通勤风险"
            )
        )

    if "education_fund" in goal_set:
        items.append(
            StrategyItem(
                coverage_type="education_savings",
                recommended_sum_assured=200_000.0,
                term_years=years,
                payment_mode="annual",
                beneficiary=beneficiary,
                rationale="子女教育金长期准备，可灵活调整缴费与领取节点"
            )
        )

    if "retirement" in goal_set:
        items.append(
            StrategyItem(
                coverage_type="annuity_retirement",
                recommended_sum_assured=300_000.0,
                term_years=years,
                payment_mode="annual",
                beneficiary=beneficiary,
                rationale="补充养老金与长寿风险对冲，优先选择保证领取或增额年金"
            )
        )

    return items


def heuristic_generate_strategy(req: UserRequest, context_docs: Optional[List[str]] = None) -> StrategyRecommendation:
    items = _infer_items_by_goal(req)

    purchase_plan = [
        PurchaseStep(phase="now", actions=["优先配置医疗与重疾，锁定健康与费率"],),
        PurchaseStep(phase="6m", actions=["补足收入保障（定寿/意外）并复核预算"],),
        PurchaseStep(phase="12m", actions=["根据收入变动追加教育金/养老金"],),
        PurchaseStep(phase="upgrade", actions=["健康状况良好时升级医疗或增加免赔计划"],),
    ]

    policy_combo_explanation = (
        "医疗报销负责短期高额支出；重疾一次性给付应对康复期；定寿覆盖家庭收入中断；"
        "意外补足突发风险；教育/养老金承担长期目标，整体互补避免重复与缺口。"
    )

    renewal = [
        "体检与健康告知变动需及时通知",
        "关注续保条件与等待期，避免断保",
        "保费日历提醒，避免逾期终止",
    ]
    claims = [
        "出险后第一时间报案并保留票据",
        "就医前确认医院/项目可报销范围",
        "理赔材料按清单备齐并复印留档",
    ]

    # 基础风险提示，详细化由风控 Agent 再补充
    risk_warnings = [
        RiskWarning(segment="健康告知", level="medium", advice="如近一年体检异常，请先评估核保可行性"),
        RiskWarning(segment="预算控制", level="low", advice="保费不宜超过年收入10%，定期复核"),
    ]

    references = []
    if context_docs:
        references = [f"KB:{i+1}" for i in range(min(5, len(context_docs)))]

    return StrategyRecommendation(
        items=items,
        purchase_plan=purchase_plan,
        policy_combo_explanation=policy_combo_explanation,
        renewal_and_claims={"renewal": renewal, "claims": claims},
        risk_warnings=risk_warnings,
        assumptions=[
            "以保额与责任完整性优先，其次兼顾预算",
            "若核保受限，则按可核保产品替代并降低杠杆"
        ],
        references=references,
    )


class StrategyGenerator:
    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm = llm_client or LLMClient()

    def generate(self, req: UserRequest, context_docs: Optional[List[str]] = None) -> StrategyRecommendation:
        # 在有可用 LLM 时，可将 heuristic 输出作为结构提示，融合 LLM 文本增强
        base = heuristic_generate_strategy(req, context_docs)
        return base

    async def agenerate(self, req: UserRequest, context_docs: Optional[List[str]] = None) -> StrategyRecommendation:
        return await asyncio.to_thread(self.generate, req, context_docs) 
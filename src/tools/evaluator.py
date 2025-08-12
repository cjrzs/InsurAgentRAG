from __future__ import annotations

from typing import List, Tuple

from ..models.schemas import UserRequest, StrategyRecommendation, RiskWarning


def assess_budget(req: UserRequest, rec: StrategyRecommendation) -> List[RiskWarning]:
    income = req.finance.annual_income or 0
    # 粗略估算：定寿0.1%-0.3%，重疾1%-2%，医疗0.1%-0.5%，意外0.02%-0.05%
    rate_map = {
        "term_life": 0.002,
        "critical_illness": 0.015,
        "medical": 0.003,
        "accident": 0.0004,
        "education_savings": 0.005,
        "annuity_retirement": 0.004,
    }
    est = 0.0
    for item in rec.items:
        est += rate_map.get(item.coverage_type, 0.003) * item.recommended_sum_assured
    warnings: List[RiskWarning] = []
    if income > 0:
        ratio = est / max(1.0, income)
        if ratio > 0.1:
            warnings.append(
                RiskWarning(
                    segment="预算控制",
                    level="high",
                    advice=f"预计年保费约为收入的{ratio:.1%}，建议不超过10%，可下调保额或分期配置",
                )
            )
        elif ratio > 0.08:
            warnings.append(
                RiskWarning(
                    segment="预算控制",
                    level="medium",
                    advice=f"预计年保费约为收入的{ratio:.1%}，略高，建议监控现金流并分批配置",
                )
            )
    return warnings


def assess_gaps(req: UserRequest, rec: StrategyRecommendation) -> List[RiskWarning]:
    goals = set(req.goals.goals)
    types = {i.coverage_type for i in rec.items}
    warns: List[RiskWarning] = []
    if "medical_expense" in goals and "medical" not in types:
        warns.append(RiskWarning(segment="保障缺口", level="high", advice="未配置医疗报销，建议优先增加"))
    if "income_protection" in goals and "term_life" not in types:
        warns.append(RiskWarning(segment="保障缺口", level="high", advice="未配置定期寿险，建议尽快补足"))
    if req.insured.age > 55 and "critical_illness" in goals and "critical_illness" not in types:
        warns.append(RiskWarning(segment="年龄与核保", level="medium", advice="重疾投保年龄偏高，核保难度上升，尽快配置"))
    return warns


def build_renewal_claims_tips() -> Tuple[List[str], List[str]]:
    renewal = [
        "到期前30日与保司确认续保条件",
        "保单地址/联系方式变更需及时更新",
        "年度保单体检/核保复核按时完成",
    ]
    claims = [
        "出险后48小时内报案，留存影像与票据",
        "需要转院/特殊项目前与客服沟通确认",
        "按保单条款清单提交资料并留底",
    ]
    return renewal, claims 
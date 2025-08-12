from __future__ import annotations

import json

from .models.schemas import UserRequest, InsuredInfo, FinancialStatus, InsuranceGoal
from .pipeline import run_pipeline


def demo_request() -> UserRequest:
    return UserRequest(
        insured=InsuredInfo(
            age=35,
            gender="male",
            occupation="软件工程师",
            health_status="良好",
            family_structure="已婚，一孩",
            smoker=False,
            city="上海",
        ),
        finance=FinancialStatus(
            annual_income=300000,
            liabilities=200000,
            assets=1500000,
            monthly_budget_for_insurance=2000,
        ),
        goals=InsuranceGoal(goals=[
            "income_protection",
            "medical_expense",
            "critical_illness",
            "education_fund",
        ]),
        existing_policies=[],
        knowledge_hints=["重疾", "医疗", "收入保障"],
    )


if __name__ == "__main__":
    req = demo_request()
    rec = run_pipeline(req)
    print(json.dumps(rec.model_dump(), ensure_ascii=False, indent=2))
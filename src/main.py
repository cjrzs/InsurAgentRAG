from __future__ import annotations

import json

from .models.schemas import UserRequest, InsuredInfo, FinancialStatus, InsuranceGoal
from .graph.pipeline_graph import PipelineGraph
import asyncio


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


async def amain() -> None:
    req = demo_request()
    out = await PipelineGraph().arun(req)
    final_json = out.get("final_json")
    print(json.dumps({"raw": final_json}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(amain())
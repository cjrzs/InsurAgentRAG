from __future__ import annotations

from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field, validator


class InsuredInfo(BaseModel):
    age: int = Field(..., ge=0, le=120)
    gender: Literal["male", "female", "other"]
    occupation: str
    health_status: str
    family_structure: str
    smoker: bool = False
    city: Optional[str] = None


class FinancialStatus(BaseModel):
    annual_income: float = Field(..., ge=0)
    liabilities: float = 0.0
    assets: float = 0.0
    monthly_budget_for_insurance: Optional[float] = Field(default=None, ge=0)


class InsuranceGoal(BaseModel):
    goals: List[
        Literal[
            "income_protection",
            "medical_expense",
            "education_fund",
            "wealth_legacy",
            "critical_illness",
            "accident",
            "retirement",
        ]
    ]


class ExistingPolicy(BaseModel):
    company: Optional[str] = None
    product: str
    coverage_type: str
    sum_assured: float = Field(..., ge=0)
    term_years: Optional[int] = None
    premium_annual: Optional[float] = Field(default=None, ge=0)


class StrategyItem(BaseModel):
    coverage_type: str
    recommended_sum_assured: float = Field(..., ge=0)
    term_years: int = Field(..., ge=1)
    payment_mode: Literal["annual", "semi-annual", "quarterly", "monthly", "single"]
    beneficiary: str
    rationale: str


class PurchaseStep(BaseModel):
    phase: Literal["now", "6m", "12m", "upgrade"]
    actions: List[str]


class RiskWarning(BaseModel):
    segment: str
    level: Literal["low", "medium", "high"]
    advice: str


class StrategyRecommendation(BaseModel):
    items: List[StrategyItem]
    purchase_plan: List[PurchaseStep]
    policy_combo_explanation: str
    renewal_and_claims: Dict[str, List[str]]  # {"renewal": [...], "claims": [...]} 
    risk_warnings: List[RiskWarning]
    assumptions: Optional[List[str]] = None
    references: Optional[List[str]] = None


class UserRequest(BaseModel):
    insured: InsuredInfo
    finance: FinancialStatus
    goals: InsuranceGoal
    existing_policies: List[ExistingPolicy] = []
    knowledge_hints: Optional[List[str]] = None 
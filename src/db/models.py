from __future__ import annotations

from typing import Optional, List
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import create_engine, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from ..config import get_database_url
from ..models.schemas import (
    InsuredInfo, FinancialStatus, InsuranceGoal, ExistingPolicy, UserRequest
)
import asyncio


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    age: Mapped[int]
    gender: Mapped[str] = mapped_column(String(10))
    occupation: Mapped[str] = mapped_column(String(128))
    health_status: Mapped[str] = mapped_column(String(128))
    family_structure: Mapped[str] = mapped_column(String(128))
    smoker: Mapped[int] = mapped_column(Integer, default=0)
    city: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    annual_income: Mapped[float] = mapped_column(Float)
    liabilities: Mapped[float] = mapped_column(Float, default=0.0)
    assets: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_budget_for_insurance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    goals: Mapped[str] = mapped_column(String(256))  # 逗号分隔

    policies: Mapped[List["Policy"]] = relationship(back_populates="user")


class Policy(Base):
    __tablename__ = "policies"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    company: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    product: Mapped[str] = mapped_column(String(128))
    coverage_type: Mapped[str] = mapped_column(String(64))
    sum_assured: Mapped[float] = mapped_column(Float)
    term_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    premium_annual: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    user: Mapped[User] = relationship(back_populates="policies")


_engine = create_engine(get_database_url(), echo=False)
Base.metadata.create_all(_engine)


def _to_user_request(u: User, ps: List[Policy]) -> UserRequest:
    insured = InsuredInfo(
        age=u.age,
        gender=u.gender,  # type: ignore
        occupation=u.occupation,
        health_status=u.health_status,
        family_structure=u.family_structure,
        smoker=bool(u.smoker),
        city=u.city,
    )
    finance = FinancialStatus(
        annual_income=u.annual_income,
        liabilities=u.liabilities,
        assets=u.assets,
        monthly_budget_for_insurance=u.monthly_budget_for_insurance,
    )
    goals = InsuranceGoal(goals=[g.strip() for g in (u.goals or "").split(",") if g.strip()])
    existing = [
        ExistingPolicy(
            company=p.company,
            product=p.product,
            coverage_type=p.coverage_type,
            sum_assured=p.sum_assured,
            term_years=p.term_years,
            premium_annual=p.premium_annual,
        )
        for p in ps
    ]
    return UserRequest(insured=insured, finance=finance, goals=goals, existing_policies=existing)


def fetch_user_request(user_id: int) -> Optional[UserRequest]:
    with Session(_engine) as s:
        u = s.get(User, user_id)
        if not u:
            return None
        ps = s.query(Policy).filter(Policy.user_id == user_id).all()
        return _to_user_request(u, ps)

async def afetch_user_request(user_id: int) -> Optional[UserRequest]:
    return await asyncio.to_thread(fetch_user_request, user_id) 
"""
FeasibilityOS AI - Funding Engine
Matches a project to Saudi government / quasi-government funding
programs based on industry, company stage, and project attributes.

This replaces the V1 stub (which returned every program for every
industry) with a simple, transparent scoring model. It is intentionally
rule-based rather than an ML model so the reasoning is explainable,
per the platform's "Explainable AI" development principle.
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class FundingProgram:
    code: str
    name: str
    focus_industries: List[str]
    stages: List[str]  # e.g. idea, mvp, early_revenue, growth
    description: str


PROGRAMS: List[FundingProgram] = [
    FundingProgram(
        code="NTDP",
        name="National Technology Development Program",
        focus_industries=["technology", "ai", "software", "fintech", "saas"],
        stages=["idea", "mvp", "early_revenue"],
        description="Supports tech-driven ventures with grants and acceleration.",
    ),
    FundingProgram(
        code="MONSHAAT",
        name="Monsha'at (SME General Authority)",
        focus_industries=["general", "retail", "services", "manufacturing"],
        stages=["idea", "mvp", "early_revenue", "growth"],
        description="Broad SME support: licensing, funding facilitation, advisory.",
    ),
    FundingProgram(
        code="CODE",
        name="Center of Digital Excellence",
        focus_industries=["technology", "ai", "digital", "software"],
        stages=["mvp", "early_revenue", "growth"],
        description="Digital transformation and technology commercialization support.",
    ),
    FundingProgram(
        code="SVC",
        name="Saudi Venture Capital Company",
        focus_industries=["technology", "ai", "fintech", "healthcare", "logistics"],
        stages=["early_revenue", "growth"],
        description="Equity co-investment through VC funds for high-growth startups.",
    ),
    FundingProgram(
        code="KAFALAH",
        name="Kafalah Program (SME Loan Guarantee)",
        focus_industries=["general", "manufacturing", "retail", "industrial"],
        stages=["early_revenue", "growth"],
        description="Government-backed loan guarantees to reduce bank lending risk.",
    ),
    FundingProgram(
        code="RDIA",
        name="Research, Development and Innovation Authority",
        focus_industries=["ai", "technology", "industrial", "healthcare", "education"],
        stages=["idea", "mvp"],
        description="R&D grants for innovation-heavy, IP-generating projects.",
    ),
]


@dataclass
class MatchResult:
    program: str
    name: str
    score_percent: float
    reasons: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)


def match(industry: str, stage: str = "idea", has_mvp: bool = False, has_technical_team: bool = True) -> List[Dict]:
    """
    Score every program against the project's profile.
    Returns results sorted by score (highest first), each with the
    reasons that drove the score and what's missing to improve it.
    """
    industry_norm = industry.strip().lower()
    results: List[MatchResult] = []

    for program in PROGRAMS:
        score = 0.0
        reasons = []
        missing = []

        if industry_norm in program.focus_industries:
            score += 60
            reasons.append(f"Industry '{industry}' matches {program.code} focus areas")
        elif "general" in program.focus_industries:
            score += 25
            reasons.append(f"{program.code} supports general/cross-sector SMEs")
        else:
            missing.append(f"Industry '{industry}' is outside {program.code}'s typical focus")

        if stage in program.stages:
            score += 25
            reasons.append(f"Project stage '{stage}' is within {program.code}'s supported range")
        else:
            missing.append(f"Stage '{stage}' is not typically funded by {program.code}")

        if has_mvp:
            score += 10
            reasons.append("MVP validation strengthens the application")
        else:
            missing.append("MVP validation not yet available")

        if has_technical_team:
            score += 5
            reasons.append("Technical team in place")
        else:
            missing.append("Technical team requirements not yet met")

        results.append(MatchResult(
            program=program.code,
            name=program.name,
            score_percent=min(round(score, 1), 100.0),
            reasons=reasons,
            missing=missing,
        ))

    results.sort(key=lambda r: r.score_percent, reverse=True)
    return [r.__dict__ for r in results]

"""
Financing Structure Service (Phase 20: Wave 2 — Funding Intelligence Capstone).

Deterministic synthesis of capital structure (Sources & Uses of Funds) for a
feasibility study, integrating:
- Funding Gap (Capex, Project Investment, Owner Capital, Existing Facilities)
- Borrowing Capacity (Safe Debt Capacity, Primary Constraints)
- Collateral (Market Value, Encumbrance, Net Available Collateral)
- Matched Verified Funding Programs (Phase 18/19 Registry & Matching)

Rules & Safeguards:
- Pure deterministic calculations; no invented interest rates or repayment terms.
- No lender approval guarantee claims.
- Sources & Uses must transparently reconcile against total project cost.
- Produces explicit warnings for funding shortfalls, overleveraging, or low equity.
- Generates actionable, sequential next steps for funding preparation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app import models
from app.services.funding_gap import compute_funding_gap
from app.services.borrowing_capacity import estimate_borrowing_capacity
from app.services.collateral import summarize_collateral
from app.services.funding_matching import evaluate_study_funding_matches

DISCLAIMER_AR = (
    "هيكل التمويل ومصادر واستخدامات الأموال المعروضة هي نموذج استرشادي مبني على القواعد "
    "المعلنة واشتراطات الملاءة المالية، ولا تمثل موافقة تمويلية أو التزاماً بنكياً."
)
DISCLAIMER_EN = (
    "The financing structure and Sources & Uses model is an advisory screening framework "
    "based on published official guidelines and solvency metrics. It does not constitute credit approval or funding commitment."
)

RECOMMENDED_MIN_EQUITY_RATIO = 0.20  # Typical minimum equity required by Saudi development funds (SDB, SIDF, etc.)


def compute_financing_structure(
    db: Session,
    *,
    study: models.FeasibilityStudy,
    project: models.Project,
    owner_contribution: Optional[float] = None,
    capex_assumption: Optional[float] = None,
    existing_facilities: Optional[float] = None,
    financial_period_dict: Optional[dict] = None,
    collateral_dicts: Optional[List[dict]] = None,
) -> Dict[str, Any]:
    """Computes a deterministic, reconciled Sources & Uses financing structure."""

    # 1. Compute Funding Gap
    project_investment = float(project.investment or 0.0) if project else 0.0
    gap_data = compute_funding_gap(
        capex_assumption=capex_assumption,
        project_investment=project_investment,
        owner_contribution=owner_contribution,
        existing_facilities=existing_facilities,
    )

    total_requirement = float(gap_data["total_project_requirement"])
    owner_equity = float(gap_data["owner_available_capital"])
    existing_debt = float(gap_data.get("existing_available_facilities") or gap_data.get("existing_facilities") or 0.0)
    initial_gap = float(gap_data["funding_gap"])

    # 2. Financial Profile & Borrowing Capacity
    safe_debt_capacity = 0.0
    capacity_status = "NO_DATA"
    annual_revenue = None
    if financial_period_dict:
        annual_revenue = float(financial_period_dict.get("revenue") or 0.0)
        ebitda = float(financial_period_dict.get("ebitda") or 0.0)
        tot_debt = float(financial_period_dict.get("total_debt") or financial_period_dict.get("long_term_debt") or 0.0)
        debt_service = float(financial_period_dict.get("debt_service") or 0.0)
        cap_eval = estimate_borrowing_capacity(
            ebitda=ebitda if ebitda else None,
            existing_debt=tot_debt if tot_debt else None,
            annual_debt_service=debt_service if debt_service else None,
        )
        capacity_status = cap_eval.get("status", "INSUFFICIENT_DATA")
        if capacity_status == "CALCULATED":
            safe_debt_capacity = float(cap_eval.get("base_capacity") or 0.0)

    # 3. Collateral Summary
    collateral_list = collateral_dicts or []
    collateral_summary = summarize_collateral(collateral_list)
    available_collateral = float(collateral_summary.get("total_verified_value") or 0.0)
    total_reported_collateral = float(collateral_summary.get("total_reported_value") or 0.0)

    # 4. Matched Programs Evaluation
    matches_data = evaluate_study_funding_matches(
        db,
        study=study,
        project=project,
        owner_contribution=owner_equity,
        capex_assumption=capex_assumption,
        existing_facilities=existing_debt,
        financial_period_dict=financial_period_dict,
        collateral_dicts=collateral_dicts,
    )

    all_matches = matches_data.get("matches", [])
    eligible_programs = [m for m in all_matches if m.get("overall_match_status") in ("MATCH", "POSSIBLE_MATCH")]

    # 5. Program Allocations Strategy
    # Allocate matched debt programs against the initial funding gap up to program maximums
    allocated_program_debt = 0.0
    program_allocations = []

    remaining_gap_to_fund = initial_gap
    for prog in eligible_programs:
        if remaining_gap_to_fund <= 0:
            break
        p_max = float(prog.get("financing_max") or remaining_gap_to_fund)
        # Cap allocation to either program max or remaining gap
        allocation = min(remaining_gap_to_fund, p_max)
        if allocation > 0:
            allocated_program_debt += allocation
            remaining_gap_to_fund -= allocation
            program_allocations.append({
                "program_id": prog["program_id"],
                "program_slug": prog["program_slug"],
                "provider": prog["provider"],
                "provider_ar": prog["provider_ar"],
                "program_name_ar": prog["program_name_ar"],
                "program_name_en": prog["program_name_en"],
                "program_type": prog["program_type"],
                "match_status": prog["overall_match_status"],
                "allocated_amount": allocation,
                "term_months": prog.get("term_months"),
                "grace_period_months": prog.get("grace_period_months"),
                "official_source_url": prog.get("official_source_url"),
            })

    # Total Identified Sources
    total_identified_sources = owner_equity + existing_debt + allocated_program_debt
    residual_gap = max(0.0, total_requirement - total_identified_sources)
    surplus = max(0.0, total_identified_sources - total_requirement)

    # Structure Metrics & Ratios
    equity_pct = (owner_equity / total_requirement) if total_requirement > 0 else 0.0
    debt_amount = existing_debt + allocated_program_debt
    debt_pct = (debt_amount / total_requirement) if total_requirement > 0 else 0.0
    de_ratio = round(debt_amount / owner_equity, 2) if owner_equity > 0 else None
    collateral_coverage = (available_collateral / debt_amount) if debt_amount > 0 else 1.0

    # 6. Uses of Funds Breakdown
    uses = [
        {
            "category_key": "capex",
            "name_ar": "النفقات الرأسمالية والتجهيزات",
            "name_en": "Capital Expenditure & Setup",
            "amount": float(capex_assumption or total_requirement),
            "percentage": round(((capex_assumption or total_requirement) / total_requirement) * 100, 1) if total_requirement > 0 else 100.0,
        }
    ]

    # 7. Sources of Funds Breakdown
    sources = [
        {
            "source_key": "owner_equity",
            "name_ar": "رأس مال المالك (المساهمة الذاتية)",
            "name_en": "Owner Equity Contribution",
            "source_type": "EQUITY",
            "amount": owner_equity,
            "percentage": round(equity_pct * 100, 1),
            "is_secured": True,
        }
    ]
    if existing_debt > 0:
        sources.append({
            "source_key": "existing_facilities",
            "name_ar": "تسهيلات قائمة معتمدة",
            "name_en": "Existing Available Credit Facilities",
            "source_type": "EXISTING_DEBT",
            "amount": existing_debt,
            "percentage": round((existing_debt / total_requirement) * 100, 1) if total_requirement > 0 else 0.0,
            "is_secured": True,
        })
    for pa in program_allocations:
        sources.append({
            "source_key": f"program_{pa['program_id']}",
            "name_ar": f"{pa['provider_ar']} — {pa['program_name_ar']}",
            "name_en": f"{pa['provider']} — {pa['program_name_en']}",
            "source_type": "PROGRAM_DEBT",
            "amount": pa["allocated_amount"],
            "percentage": round((pa["allocated_amount"] / total_requirement) * 100, 1) if total_requirement > 0 else 0.0,
            "is_secured": False,
            "program_slug": pa["program_slug"],
            "official_source_url": pa["official_source_url"],
        })
    if residual_gap > 0:
        sources.append({
            "source_key": "residual_gap",
            "name_ar": "فجوة تمويل متبقية (غير مغطاة)",
            "name_en": "Residual Unfunded Gap",
            "source_type": "UNFUNDED",
            "amount": residual_gap,
            "percentage": round((residual_gap / total_requirement) * 100, 1) if total_requirement > 0 else 0.0,
            "is_secured": False,
        })

    # 8. Deterministic Warnings & Alerts
    warnings = []
    if residual_gap > 0:
        warnings.append({
            "code": "RESIDUAL_GAP_EXISTS",
            "severity": "CRITICAL",
            "title_ar": "توجد فجوة تمويلية غير مغطاة",
            "title_en": "Unfunded Residual Funding Gap",
            "message_ar": f"هناك عجز تمويلي قدره {residual_gap:,.0f} ر.س ({residual_gap/total_requirement*100:.1f}%) يتطلب زيادة مساهمة المالك أو إدخال شركاء أو خفض التكاليف.",
            "message_en": f"An unfunded gap of {residual_gap:,.0f} SAR ({residual_gap/total_requirement*100:.1f}%) remains; requires additional equity, partners, or cost reduction.",
        })

    if equity_pct < RECOMMENDED_MIN_EQUITY_RATIO:
        shortfall = (RECOMMENDED_MIN_EQUITY_RATIO * total_requirement) - owner_equity
        warnings.append({
            "code": "LOW_OWNER_EQUITY",
            "severity": "WARNING",
            "title_ar": "نسبة المساهمة الذاتية أقل من المعايير التنموية",
            "title_en": "Owner Equity Below Benchmark",
            "message_ar": f"المساهمة الذاتية الحالية ({equity_pct*100:.1f}%) أقل من الحد الأدنى الشائع (20%). العجز للوصول إلى النسبة هو {shortfall:,.0f} ر.س.",
            "message_en": f"Current owner equity ({equity_pct*100:.1f}%) is below the typical 20% minimum. Shortfall is {shortfall:,.0f} SAR.",
        })

    if safe_debt_capacity > 0 and debt_amount > safe_debt_capacity:
        excess_debt = debt_amount - safe_debt_capacity
        warnings.append({
            "code": "EXCEEDS_SAFE_DEBT_CAPACITY",
            "severity": "WARNING",
            "title_ar": "إجمالي المديونية يتجاوز طاقة الاستدانة الآمنة",
            "title_en": "Total Debt Exceeds Safe Capacity",
            "message_ar": f"إجمالي التمويل المطلوب ({debt_amount:,.0f} ر.س) يتجاوز طاقة الاستدانة التقديرية الآمنة ({safe_debt_capacity:,.0f} ر.س) بفارق {excess_debt:,.0f} ر.س.",
            "message_en": f"Total required debt ({debt_amount:,.0f} SAR) exceeds assessed safe borrowing capacity ({safe_debt_capacity:,.0f} SAR) by {excess_debt:,.0f} SAR.",
        })

    if debt_amount > 0 and available_collateral < debt_amount:
        # Check if any allocated program provides Kafalah guarantee
        has_guarantee = any(pa["program_type"] == "GUARANTEE" or "كفالة" in pa["provider_ar"] for pa in program_allocations)
        if not has_guarantee:
            warnings.append({
                "code": "COLLATERAL_SHORTFALL",
                "severity": "ADVISORY",
                "title_ar": "تغطية الضمانات العينية للمديونية جزئية",
                "title_en": "Partial Collateral Coverage",
                "message_ar": f"الضمانات الموثقة ({available_collateral:,.0f} ر.س) تغطي {collateral_coverage*100:.1f}% من إجمالي الدين. يوصى ببرامج كفالة لسد العجز.",
                "message_en": f"Verified collateral ({available_collateral:,.0f} SAR) covers {collateral_coverage*100:.1f}% of total debt. Kafalah guarantees recommended.",
            })

    # 9. Deterministic Next Actions Checklist
    next_actions = [
        {
            "step_number": 1,
            "title_ar": "تجهيز السجل التجاري والقوائم المالية المعتمدة",
            "title_en": "Prepare Commercial Registration & Audited Financial Statements",
            "status": "READY" if annual_revenue is not None else "ACTION_REQUIRED",
            "description_ar": "التأكد من سريان السجل التجاري وإيداع القوائم المالية عبر منصة قوائم.",
            "description_en": "Ensure valid Commercial Registration (CR) and deposited statements via Qawaem platform.",
        },
        {
            "step_number": 2,
            "title_ar": "توثيق صكوك وتقييمات الأصول الضامنة",
            "title_en": "Verify Collateral Deeds & Certified Valuations",
            "status": "READY" if available_collateral > 0 else "PENDING_VALUATION",
            "description_ar": "الحصول على تقييم عقاري أو أصول معتمد من مقيّم مرخص من الهيئة السعودية للمقيّمين المعتمدين (تقييم).",
            "description_en": "Obtain certified property or asset valuation from a TAQEEM accredited valuer.",
        },
        {
            "step_number": 3,
            "title_ar": "تأكيد إيداع المساهمة الذاتية في الحساب البنكي",
            "title_en": "Confirm Owner Equity Deposit in Dedicated Bank Account",
            "status": "READY" if owner_equity >= (0.20 * total_requirement) else "ACTION_REQUIRED",
            "description_ar": "إثبات كفاية السيولة النقدية أو الأصول العينية كرأس مال مالك لتفادي رفض طلب التمويل.",
            "description_en": "Provide bank statement proof of owner capital to fulfill mandatory equity requirements.",
        },
        {
            "step_number": 4,
            "title_ar": "التقديم عبر البوابات الرسمية للبرامج المتطابقة",
            "title_en": "Apply via Official Portals of Matched Programs",
            "status": "ELIGIBLE" if len(eligible_programs) > 0 else "NO_MATCH",
            "description_ar": f"تم تحديد {len(eligible_programs)} برنامج تمويلي مطابق؛ ابدأ التقديم عبر بوابة النفاذ الوطني الرسمية لكل جهة.",
            "description_en": f"{len(eligible_programs)} matching funding program(s) identified; apply directly via official portals.",
        },
    ]

    return {
        "study_id": study.id,
        "project_name": project.name if project else "",
        "sector": project.industry if project else "general",
        "stage": project.stage if project else "startup",
        "total_project_requirement": total_requirement,
        "owner_equity": owner_equity,
        "existing_debt": existing_debt,
        "allocated_program_debt": allocated_program_debt,
        "total_identified_sources": total_identified_sources,
        "residual_gap": residual_gap,
        "surplus": surplus,
        "equity_percentage": round(equity_pct, 4),
        "debt_percentage": round(debt_pct, 4),
        "debt_to_equity_ratio": de_ratio,
        "collateral_coverage_ratio": round(collateral_coverage, 4),
        "safe_debt_capacity": safe_debt_capacity,
        "capacity_status": capacity_status,
        "sources": sources,
        "uses": uses,
        "program_allocations": program_allocations,
        "warnings": warnings,
        "next_actions": next_actions,
        "disclaimer_ar": DISCLAIMER_AR,
        "disclaimer_en": DISCLAIMER_EN,
        "version": "1.0.0",
    }

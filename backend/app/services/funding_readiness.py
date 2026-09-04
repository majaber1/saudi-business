"""
Deterministic Funding Readiness engine (Phase 17).

Evaluates whether a feasibility study / company is adequately prepared to
approach external funding providers (commercial banks, government development
funds such as SIDF/ADF, Kafalah program, etc.).

Explicitly NOT a credit approval, lender underwriting score, or loan guarantee.
Answers: "Is the company prepared to approach funding options?"
Does NOT answer: "Will a bank approve you?"

Allowed States:
  - READY: Core financials strong, debt capacity covers funding gap, owner
    equity committed, collateral verified, no critical blockers.
  - PARTIALLY_READY: Core financials exist and capacity can be estimated, but
    some supporting data, collateral verification, equity proportion, or
    capacity headroom is incomplete.
  - NEEDS_INFORMATION: Essential quantitative inputs are missing (EBITDA,
    annual debt service, project cost, owner contribution, or financial period).
  - NOT_READY: Profile exhibits deterministic material blockers (operating
    losses, DSCR < 1.0, severe over-leverage, or zero borrowing capacity).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.borrowing_capacity import estimate_borrowing_capacity
from app.services.collateral import summarize_collateral
from app.services.financial_health import compute_metrics, summarize
from app.services.funding_gap import compute_funding_gap

CALCULATION_VERSION = "1.0.0"

READINESS_THRESHOLDS = {
    "min_dscr_ready": 1.25,
    "min_dscr_acceptable": 1.0,
    "max_leverage_ready": 4.0,
    "max_leverage_acceptable": 5.0,
    "min_owner_equity_pct": 0.15,
}

STATUS_READY = "READY"
STATUS_PARTIALLY_READY = "PARTIALLY_READY"
STATUS_NEEDS_INFO = "NEEDS_INFORMATION"
STATUS_NOT_READY = "NOT_READY"


def evaluate_funding_readiness(
    *,
    study_id: int,
    project_investment: float,
    capex_assumption: Optional[float] = None,
    owner_contribution: Optional[float] = None,
    existing_facilities: Optional[float] = None,
    financial_period: Optional[dict] = None,
    prior_period: Optional[dict] = None,
    collateral_records: Optional[List[dict]] = None,
) -> Dict[str, Any]:
    """Pure deterministic evaluation of funding readiness from real outputs.

    Consumes Company Financial Profile, Financial Health, Funding Gap,
    Borrowing Capacity, and Collateral without fabricating arbitrary scores
    or credit approvals.
    """
    positive_factors: List[str] = []
    positive_factors_ar: List[str] = []
    blocking_factors: List[str] = []
    blocking_factors_ar: List[str] = []
    missing_info: List[str] = []
    missing_info_ar: List[str] = []
    warnings: List[str] = []
    warnings_ar: List[str] = []
    actionable_steps: List[Dict[str, str]] = []

    # 1. Compute Funding Gap
    funding_gap_res = compute_funding_gap(
        capex_assumption=capex_assumption,
        project_investment=project_investment,
        owner_contribution=owner_contribution,
        existing_facilities=existing_facilities,
    )
    total_req = funding_gap_res["total_project_requirement"]
    gap_amount = funding_gap_res["funding_gap"]
    owner_cap = funding_gap_res["owner_available_capital"]

    # 2. Check Project & Gap completeness
    if total_req <= 0:
        missing_info.append("Total project investment requirement is not defined or non-positive.")
        missing_info_ar.append("إجمالي احتياج المشروع الاستثماري غير محدد أو غير موجب.")
        actionable_steps.append({
            "key": "set_project_cost",
            "title_en": "Define project investment cost or capex assumption",
            "title_ar": "تحديد تكلفة المشروع أو افتراض النفقات الرأسمالية",
            "action_target": "funding_gap",
        })

    if owner_contribution is None:
        missing_info.append("Owner equity contribution is not recorded in study assumptions.")
        missing_info_ar.append("المساهمة الذاتية من المالك غير مسجّلة في افتراضات الدراسة.")
        actionable_steps.append({
            "key": "set_owner_contribution",
            "title_en": "Record owner contribution in Funding Gap",
            "title_ar": "تسجيل مساهمة المالك في قسم فجوة التمويل",
            "action_target": "funding_gap",
        })

    # 3. Check Financial Period & Core Financial Inputs
    health_snapshot: Optional[Dict[str, Any]] = None
    capacity_snapshot: Optional[Dict[str, Any]] = None

    if financial_period is None:
        missing_info.append("Company financial statements or period data have not been recorded.")
        missing_info_ar.append("لم يتم تسجيل أي قوائم أو فترات مالية فعلية للشركة.")
        actionable_steps.append({
            "key": "add_financial_period",
            "title_en": "Add financial period in Company Financial Profile",
            "title_ar": "إضافة فترة مالية في البيانات المالية للشركة",
            "action_target": "financial_data",
        })
    else:
        ebitda = financial_period.get("ebitda")
        debt_service = financial_period.get("annual_debt_service")
        existing_debt = financial_period.get("existing_debt")

        if ebitda is None:
            missing_info.append("Operating earnings (EBITDA) is missing from recorded financial data.")
            missing_info_ar.append("الربح التشغيلي قبل الفوائد والضرائب والإهلاك (EBITDA) غير مسجّل.")
            actionable_steps.append({
                "key": "add_ebitda",
                "title_en": "Enter EBITDA in financial period",
                "title_ar": "إدخال الأرباح التشغيلية (EBITDA) في الفترة المالية",
                "action_target": "financial_data",
            })

        if debt_service is None:
            missing_info.append("Annual debt service obligations are not provided.")
            missing_info_ar.append("التزامات خدمة الدين السنوية غير مسجّلة.")
            actionable_steps.append({
                "key": "add_debt_service",
                "title_en": "Enter annual debt service in financial period",
                "title_ar": "إدخال خدمة الدين السنوية في الفترة المالية",
                "action_target": "financial_data",
            })

        # Calculate Financial Health metrics & category summary
        metrics = compute_metrics(financial_period, prior_period)
        health_summary = summarize(metrics)
        health_snapshot = {
            "period": financial_period.get("period", "Current"),
            "profitability": health_summary["profitability"],
            "liquidity": health_summary["liquidity"],
            "leverage": health_summary["leverage"],
            "debt_service_capacity": health_summary["debt_service_capacity"],
            "data_coverage": health_summary["data_coverage"],
            "dscr": metrics["dscr"].value if metrics["dscr"].value is not None else None,
            "debt_to_ebitda": metrics["debt_to_ebitda"].value if metrics["debt_to_ebitda"].value is not None else None,
            "net_margin": metrics["net_margin"].value if metrics["net_margin"].value is not None else None,
            "current_ratio": metrics["current_ratio"].value if metrics["current_ratio"].value is not None else None,
        }

        # Calculate Borrowing Capacity
        capacity_res = estimate_borrowing_capacity(
            ebitda=ebitda,
            existing_debt=existing_debt,
            annual_debt_service=debt_service,
        )
        capacity_snapshot = {
            "status": capacity_res["status"],
            "base_capacity": capacity_res["base_capacity"],
            "stress_capacity": capacity_res["stress_capacity"],
            "primary_constraint": capacity_res["primary_constraint"],
            "secondary_constraint": capacity_res["secondary_constraint"],
            "financial_support": capacity_res["financial_support"],
        }

    # 4. Collateral Snapshot
    collateral_list = collateral_records or []
    collateral_snapshot = summarize_collateral(collateral_list)

    # -------------------------------------------------------------------------
    # STATE EVALUATION
    # -------------------------------------------------------------------------

    # Path A: Missing critical information prevents readiness determination
    if missing_info:
        summary_en = (
            "Funding readiness cannot be determined yet because essential financial or project inputs are missing."
        )
        summary_ar = (
            "لا يمكن تحديد جاهزية التمويل بعد نظراً لعدم اكتمال البيانات المالية أو مدخلات المشروع الأساسية."
        )
        return {
            "study_id": study_id,
            "status": STATUS_NEEDS_INFO,
            "summary_en": summary_en,
            "summary_ar": summary_ar,
            "positive_factors": positive_factors,
            "positive_factors_ar": positive_factors_ar,
            "blocking_factors": blocking_factors,
            "blocking_factors_ar": blocking_factors_ar,
            "missing_information": missing_info,
            "missing_information_ar": missing_info_ar,
            "warnings": warnings,
            "warnings_ar": warnings_ar,
            "actionable_steps": actionable_steps,
            "financial_health_snapshot": health_snapshot,
            "funding_gap_snapshot": funding_gap_res,
            "borrowing_capacity_snapshot": capacity_snapshot,
            "collateral_snapshot": collateral_snapshot,
            "documents_status": "NOT_EVALUATED",
            "assumptions_used": READINESS_THRESHOLDS,
            "calculation_version": CALCULATION_VERSION,
        }

    # If we reached here, core financial inputs and project cost exist!
    ebitda_val = float(financial_period["ebitda"])
    debt_service_val = float(financial_period["annual_debt_service"])
    existing_debt_val = float(financial_period.get("existing_debt") or 0.0)
    base_cap = capacity_snapshot["base_capacity"] if capacity_snapshot else 0.0
    base_cap = base_cap or 0.0

    # 5. Check for Material Blockers (NOT_READY)
    # A) Negative/zero EBITDA
    if ebitda_val <= 0:
        blocking_factors.append(
            f"Operating cash generation is non-viable (EBITDA = {ebitda_val:,.0f} SAR). Positive operational earnings are required for commercial debt funding."
        )
        blocking_factors_ar.append(
            f"الأرباح التشغيلية غير قابلة للإقراض (EBITDA = {ebitda_val:,.0f} ر.س). يلزم تحقيق أرباح تشغيلية موجبة للتأهل للتمويل."
        )

    # B) Non-viable DSCR (< 1.0)
    dscr_val = ebitda_val / debt_service_val if debt_service_val > 0 else 999.0
    if debt_service_val > 0 and dscr_val < READINESS_THRESHOLDS["min_dscr_acceptable"]:
        blocking_factors.append(
            f"Existing debt service coverage is weak ({dscr_val:.2f}x DSCR), below the 1.0x break-even threshold (current operations cannot service existing debt)."
        )
        blocking_factors_ar.append(
            f"معدل تغطية خدمة الدين الحالي ضعيف ({dscr_val:.2f}x)، وهو دون نقطة التعادل 1.0x (التدفقات الحالية لا تغطي الالتزامات القائمة)."
        )

    # C) Severe over-leverage (> 5.0x)
    debt_to_ebitda = existing_debt_val / ebitda_val if ebitda_val > 0 else 999.0
    if ebitda_val > 0 and debt_to_ebitda > READINESS_THRESHOLDS["max_leverage_acceptable"]:
        blocking_factors.append(
            f"Existing leverage is excessively high ({debt_to_ebitda:.2f}x Debt/EBITDA), exceeding institutional leverage thresholds."
        )
        blocking_factors_ar.append(
            f"الرافعة المالية الحالية مرتفعة جداً ({debt_to_ebitda:.2f}x ضعف الدين إلى EBITDA)، متجاوزة السقوف الائتمانية المقبولة."
        )

    # D) Zero capacity with positive funding gap
    if base_cap <= 0 and gap_amount > 0:
        blocking_factors.append(
            "Estimated borrowing capacity is zero under current debt service and leverage constraints, but a funding gap remains."
        )
        blocking_factors_ar.append(
            "القدرة التمويلية التقديرية صفر في ظل الالتزامات القائمة، بينما توجد فجوة تمويلية مطلوبة."
        )

    if blocking_factors:
        summary_en = (
            "The current business profile contains material financial constraints that prevent approaching debt funding providers at this time."
        )
        summary_ar = (
            "الملف المالي الحالي يحتوي على محددات جوهرية تعيق التقدم لجهات التمويل الإقراضي في الوقت الراهن."
        )
        return {
            "study_id": study_id,
            "status": STATUS_NOT_READY,
            "summary_en": summary_en,
            "summary_ar": summary_ar,
            "positive_factors": positive_factors,
            "positive_factors_ar": positive_factors_ar,
            "blocking_factors": blocking_factors,
            "blocking_factors_ar": blocking_factors_ar,
            "missing_information": missing_info,
            "missing_information_ar": missing_info_ar,
            "warnings": warnings,
            "warnings_ar": warnings_ar,
            "actionable_steps": actionable_steps,
            "financial_health_snapshot": health_snapshot,
            "funding_gap_snapshot": funding_gap_res,
            "borrowing_capacity_snapshot": capacity_snapshot,
            "collateral_snapshot": collateral_snapshot,
            "documents_status": "NOT_EVALUATED",
            "assumptions_used": READINESS_THRESHOLDS,
            "calculation_version": CALCULATION_VERSION,
        }

    # -------------------------------------------------------------------------
    # 6. Evaluate Positive Factors & Warnings for Viable Cases
    # -------------------------------------------------------------------------

    # A) Debt service coverage
    if dscr_val >= 1.5:
        positive_factors.append(f"Strong debt-service coverage profile ({dscr_val:.2f}x DSCR), well above standard 1.25x target.")
        positive_factors_ar.append(f"معدل تغطية خدمة دين قوي ({dscr_val:.2f}x)، أعلى بكثير من المستهدف المعتاد 1.25x.")
    elif dscr_val >= READINESS_THRESHOLDS["min_dscr_ready"]:
        positive_factors.append(f"Acceptable debt-service coverage ratio ({dscr_val:.2f}x DSCR).")
        positive_factors_ar.append(f"معدل تغطية خدمة دين مقبول ({dscr_val:.2f}x).")
    else:
        warnings.append(
            f"Debt-service coverage ({dscr_val:.2f}x DSCR) is tight (below 1.25x target). Lenders may require debt rescheduling or personal guarantee."
        )
        warnings_ar.append(
            f"معدل تغطية خدمة الدين ({dscr_val:.2f}x) ضيق (أقل من 1.25x). قد يشترط الممولون إعادة جدولة أو كفالات إضافية."
        )

    # B) Leverage
    if debt_to_ebitda <= 2.0:
        positive_factors.append(f"Conservative existing leverage ({debt_to_ebitda:.2f}x Debt/EBITDA), leaving ample balance sheet capacity.")
        positive_factors_ar.append(f"رافعة مالية محافظة ({debt_to_ebitda:.2f}x ضعف الدين إلى EBITDA)، مما يتيح طاقة اقتراضية مريحة.")
    elif debt_to_ebitda <= READINESS_THRESHOLDS["max_leverage_ready"]:
        positive_factors.append(f"Moderate leverage ({debt_to_ebitda:.2f}x Debt/EBITDA) within standard institutional screening limits.")
        positive_factors_ar.append(f"رافعة مالية معتدلة ({debt_to_ebitda:.2f}x ضعف الدين إلى EBITDA) ضمن الحدود الائتمانية المقبولة.")
    else:
        warnings.append(
            f"Leverage is elevated ({debt_to_ebitda:.2f}x Debt/EBITDA), which may reduce the maximum loan amount offered by funders."
        )
        warnings_ar.append(
            f"الرافعة المالية مرتفعة نسبياً ({debt_to_ebitda:.2f}x ضعف الدين إلى EBITDA)، مما قد يحد من قيمة القرض الممنوح."
        )

    # C) Borrowing capacity vs Funding gap
    if gap_amount <= base_cap:
        positive_factors.append(
            f"Estimated borrowing capacity ({base_cap:,.0f} SAR) covers the required funding gap ({gap_amount:,.0f} SAR)."
        )
        positive_factors_ar.append(
            f"القدرة التمويلية التقديرية ({base_cap:,.0f} ر.س) تغطي فجوة التمويل المطلوبة ({gap_amount:,.0f} ر.س)."
        )
    else:
        warnings.append(
            f"Current estimated borrowing capacity ({base_cap:,.0f} SAR) does not fully cover the funding gap ({gap_amount:,.0f} SAR). Additional equity or co-financing will be needed."
        )
        warnings_ar.append(
            f"القدرة التمويلية التقديرية ({base_cap:,.0f} ر.س) لا تغطي كامل الفجوة التمويلية ({gap_amount:,.0f} ر.س)، ويلزم مساهمة ذاتية إضافية أو تمويل مشترك."
        )
        actionable_steps.append({
            "key": "adjust_funding_gap",
            "title_en": "Increase owner equity or review project budget",
            "title_ar": "زيادة رأس مال المالك أو مراجعة ميزانية المشروع",
            "action_target": "funding_gap",
        })

    # D) Owner equity contribution percentage
    equity_pct = owner_cap / total_req if total_req > 0 else 0.0
    if equity_pct >= 0.20:
        positive_factors.append(f"Substantial owner equity commitment ({equity_pct * 100:.1f}% of project cost, {owner_cap:,.0f} SAR).")
        positive_factors_ar.append(f"التزام ذاتي قوي من المالك ({equity_pct * 100:.1f}% من تكلفة المشروع، {owner_cap:,.0f} ر.س).")
    elif equity_pct >= READINESS_THRESHOLDS["min_owner_equity_pct"]:
        positive_factors.append(f"Owner equity contribution meets standard baseline ({equity_pct * 100:.1f}% of project cost).")
        positive_factors_ar.append(f"المساهمة الذاتية تستوفي الحد الأدنى المعتاد ({equity_pct * 100:.1f}% من تكلفة المشروع).")
    else:
        warnings.append(
            f"Owner equity contribution is low ({equity_pct * 100:.1f}%). Saudi development and commercial lenders typically expect at least 15-20% owner equity."
        )
        warnings_ar.append(
            f"المساهمة الذاتية منخفضة ({equity_pct * 100:.1f}%). تشترط برامج التمويل السعودية عادة مساهمة ذاتية لا تقل عن 15-20%."
        )
        actionable_steps.append({
            "key": "increase_owner_equity",
            "title_en": "Increase owner equity contribution to at least 15-20%",
            "title_ar": "رفع المساهمة الذاتية إلى 15-20% على الأقل",
            "action_target": "funding_gap",
        })

    # E) Collateral evaluation
    if collateral_snapshot["record_count"] == 0:
        warnings.append(
            "No collateral assets recorded. While cash-flow lending exists, unsecured facilities often carry lower borrowing limits or require Kafalah backing."
        )
        warnings_ar.append(
            "لا توجد أصول ضمانات مسجّلة. قد يتطلب التمويل غير المضمون هوامش أضيق أو دعم كفالة."
        )
        actionable_steps.append({
            "key": "add_collateral",
            "title_en": "Record business or real estate collateral in Collateral section",
            "title_ar": "تسجيل أصول الضمانات المتاحة في قسم الضمانات",
            "action_target": "collateral",
        })
    else:
        # Check verification state
        unverified_count = sum(
            1 for r in collateral_list
            if r.get("verification_status") not in ("DOCUMENT_SUPPORTED", "VERIFIED")
        )
        if unverified_count > 0:
            warnings.append(
                f"{unverified_count} collateral asset(s) are user-reported or unverified. Official appraisals and documentation will be requested by funders."
            )
            warnings_ar.append(
                f"توجد {unverified_count} من الضمانات مُبلَّغة من المستخدم أو غير موثّقة بمستند رسمي يلزم توثيقها للممولين."
            )
            actionable_steps.append({
                "key": "verify_collateral",
                "title_en": "Upload formal valuation or document for collateral",
                "title_ar": "إرفاق تقييم رسمي أو مستند داعم للضمانات",
                "action_target": "collateral",
            })
        else:
            doc_verified_val = sum(
                float(r.get("verified_value") or r.get("reported_value", 0.0))
                for r in collateral_list
                if r.get("verification_status") in ("DOCUMENT_SUPPORTED", "VERIFIED")
            )
            positive_factors.append(
                f"Collateral portfolio is fully document-supported ({collateral_snapshot['record_count']} items, {doc_verified_val:,.0f} SAR verified value)."
            )
            positive_factors_ar.append(
                f"محفظة الضمانات موثّقة بمستندات رسمية ({collateral_snapshot['record_count']} أصول، بقيمة موثّقة {doc_verified_val:,.0f} ر.س)."
            )

        # Check encumbrance
        if collateral_snapshot["unknown_encumbrance_count"] > 0:
            warnings.append(
                f"Encumbrance status is unknown for {collateral_snapshot['unknown_encumbrance_count']} collateral asset(s). Clarity on existing liens is required."
            )
            warnings_ar.append(
                f"حالة الرهن غير محددة لعدد {collateral_snapshot['unknown_encumbrance_count']} من الضمانات المسجّلة."
            )
            actionable_steps.append({
                "key": "update_encumbrance",
                "title_en": "Specify encumbrance status for all collateral items",
                "title_ar": "تحديث وتحديد حالة الرهن لجميع أصول الضمانات",
                "action_target": "collateral",
            })

    # -------------------------------------------------------------------------
    # 7. Final State Assignment: READY vs PARTIALLY_READY
    # -------------------------------------------------------------------------
    if not warnings:
        status = STATUS_READY
        summary_en = (
            "The business profile and funding plan meet core screening criteria to approach debt funding providers."
        )
        summary_ar = (
            "الملف المالي وخطة التمويل مستوفيان لمعايير الفحص الأولي للتقدم إلى جهات التمويل الإقراضي."
        )
    else:
        status = STATUS_PARTIALLY_READY
        summary_en = (
            "The study has sufficient financial data to estimate borrowing capacity, but important supporting data, collateral verification, or equity adjustments are needed before formal submission."
        )
        summary_ar = (
            "تتوفر بيانات مالية كافية لتقدير القدرة التمويلية، ولكن يلزم استكمال بعض البيانات الداعمة أو توثيق الضمانات قبل التقديم الرسمي."
        )

    return {
        "study_id": study_id,
        "status": status,
        "summary_en": summary_en,
        "summary_ar": summary_ar,
        "positive_factors": positive_factors,
        "positive_factors_ar": positive_factors_ar,
        "blocking_factors": blocking_factors,
        "blocking_factors_ar": blocking_factors_ar,
        "missing_information": missing_info,
        "missing_information_ar": missing_info_ar,
        "warnings": warnings,
        "warnings_ar": warnings_ar,
        "actionable_steps": actionable_steps,
        "financial_health_snapshot": health_snapshot,
        "funding_gap_snapshot": funding_gap_res,
        "borrowing_capacity_snapshot": capacity_snapshot,
        "collateral_snapshot": collateral_snapshot,
        "documents_status": "NOT_EVALUATED",
        "assumptions_used": READINESS_THRESHOLDS,
        "calculation_version": CALCULATION_VERSION,
    }

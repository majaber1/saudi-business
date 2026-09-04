"""Domain Service for Wave 5 Launch Execution, Actuals & Reforecasting OS.

Provides:
- Launch workspace initialization gated by validation decisions.
- Pre-launch execution milestone tracking with Saudi regulatory categories.
- Immutable baseline snapshot freezing of feasibility forecasts.
- Actual performance recording (CAPEX, OPEX breakdown, Revenue, Volume).
- Zero-denominator protected forecast vs. actual variance engine.
- Scenario-based reforecasting with runway and burn rate calculations.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app import models

# Milestone categories
CATEGORY_REGULATORY = "REGULATORY"
CATEGORY_LOCATION = "LOCATION"
CATEGORY_EQUIPMENT = "EQUIPMENT"
CATEGORY_TEAM = "TEAM"
CATEGORY_MARKETING = "MARKETING"
CATEGORY_OPERATIONS = "OPERATIONS"

# Milestone statuses
MILESTONE_PENDING = "PENDING"
MILESTONE_IN_PROGRESS = "IN_PROGRESS"
MILESTONE_COMPLETED = "COMPLETED"
MILESTONE_DELAYED = "DELAYED"

# Variance alert levels
ALERT_NO_DATA = "NO_DATA"
ALERT_NORMAL = "NORMAL"
ALERT_WATCH = "WATCH"
ALERT_MATERIAL_VARIANCE = "MATERIAL_VARIANCE"


def get_or_create_launch_workspace(
    db: Session,
    user: models.User,
    study_id: int,
) -> models.LaunchWorkspace:
    """Fetches or initializes the launch workspace for a study.
    
    Enforces validation gate: rejects launch creation if the latest validation
    decision is STOP, or requires explicit warning/conditions if PIVOT.
    """
    study = db.query(models.FeasibilityStudy).filter_by(id=study_id).first()
    if not study:
        raise ValueError(f"Feasibility study {study_id} not found")
    if study.project.owner_id != user.id:
        raise PermissionError("Access denied to feasibility study")

    # Check Validation Decision Gate
    val_ws = db.query(models.ValidationWorkspace).filter_by(study_id=study_id).first()
    if val_ws and val_ws.decisions:
        latest_dec = val_ws.decisions[0]
        if latest_dec.decision == "STOP":
            raise ValueError("لا يمكن تفعيل مساحة الإطلاق لمشروع صدر بشأنه قرار إيقاف رسمي (STOP).")
        if latest_dec.decision == "PIVOT":
            raise ValueError("المشروع بحاجة إلى استكمال دورة تعديل المسار (PIVOT) وإثبات الفرضيات أولاً قبل بدء الإطلاق.")

    ws = db.query(models.LaunchWorkspace).filter_by(study_id=study_id).first()
    if not ws:
        ws = models.LaunchWorkspace(
            study_id=study.id,
            project_id=study.project_id,
            user_id=user.id,
            status="PRE_LAUNCH",
        )
        db.add(ws)
        db.commit()
        db.refresh(ws)

        # Seed standard pre-launch execution milestones
        default_milestones = [
            (
                CATEGORY_REGULATORY,
                "إصدار السجل التجاري ورخصة بلدي وشهادة الدفاع المدني",
                "استكمال المتطلبات النظامية والتراخيص الحكومية عبر منصة بلدي ووزارة التجارة.",
                5000.0,
            ),
            (
                CATEGORY_LOCATION,
                "تحديد واستئجار الموقع التجاري وتوثيق عقد إيجار",
                "اختيار الموقع المطابق للاشتراطات الفنية وتوقيع العقد عبر شبكة إيجار.",
                75000.0,
            ),
            (
                CATEGORY_EQUIPMENT,
                "شراء وتوريد وتجهيز المعدات وخطوط الإنتاج",
                "التعاقد مع الموردين المعتمدين وتركيب التجهيزات الأساسية لنشاط المشروع.",
                120000.0,
            ),
            (
                CATEGORY_TEAM,
                "استقطاب وتوظيف الكفاءات وتحقيق نسب التوطين عبر قوى",
                "إصدار التأشيرات أو التعاقد المحلي وتوثيق عقود العمل في منصة قوى.",
                25000.0,
            ),
            (
                CATEGORY_MARKETING,
                "تنفيذ الحملة التسويقية والافتتاح التجريبي (Soft Launch)",
                "حملة إعلانية رقمية واختبار العمليات التشغيلية وتجربة العميل قبل الافتتاح الرسمي.",
                15000.0,
            ),
            (
                CATEGORY_OPERATIONS,
                "الافتتاح الرسمي والتشغيل الكامل (Grand Opening)",
                "إطلاق المبيعات الكامل وربط الفوترة الإلكترونية (ZATCA) وأجهزة نقاط البيع.",
                10000.0,
            ),
        ]

        for cat, title, desc, budget in default_milestones:
            m = models.LaunchMilestone(
                workspace_id=ws.id,
                category=cat,
                title=title,
                description=desc,
                budget_allocated=budget,
                status=MILESTONE_PENDING,
            )
            db.add(m)

        # Create Baseline Snapshot v1 from study financials without mutating original study
        investment_total = float(study.project.investment if (study.project and study.project.investment) else ((study.payload or {}).get("investment") or 0.0))
        # Generate 12 baseline monthly projections based on initial study investment
        # Indicative baseline curve: ramp-up in revenue, stable capex in M1, operational opex
        base_monthly_rev = round((investment_total * 0.15) if investment_total > 0 else 50000.0, 2)
        base_monthly_opex = round((investment_total * 0.08) if investment_total > 0 else 25000.0, 2)
        projections = []
        for m_idx in range(1, 13):
            # Gradual ramp: 50% month 1, reaching 100% by month 6
            ramp = min(1.0, 0.5 + (m_idx - 1) * 0.1)
            m_rev = round(base_monthly_rev * ramp, 2)
            m_opex = base_monthly_opex
            m_capex = investment_total * 0.8 if m_idx == 1 else 0.0
            projections.append({
                "month": m_idx,
                "period_label": f"M{m_idx:02d}",
                "projected_revenue": m_rev,
                "projected_capex": m_capex,
                "projected_opex": m_opex,
                "projected_net_cashflow": round(m_rev - m_capex - m_opex, 2),
            })

        snapshot = models.LaunchBaselineSnapshot(
            workspace_id=ws.id,
            snapshot_version=1,
            total_investment=investment_total,
            monthly_projections=projections,
            source_study_revision=study.revision,
            notes="نسخة أساسية مجمدة من دراسة الجدوى الأولية عند بدء الإطلاق.",
        )
        db.add(snapshot)
        db.commit()
        db.refresh(ws)

    return ws


def add_launch_milestone(
    db: Session,
    workspace_id: int,
    user: models.User,
    category: str,
    title: str,
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    budget_allocated: Optional[float] = None,
) -> models.LaunchMilestone:
    """Adds a custom milestone to the launch workspace."""
    ws = db.query(models.LaunchWorkspace).filter_by(id=workspace_id).first()
    if not ws or ws.user_id != user.id:
        raise PermissionError("Access denied to launch workspace")

    m = models.LaunchMilestone(
        workspace_id=ws.id,
        category=category,
        title=title,
        description=description,
        due_date=due_date,
        budget_allocated=budget_allocated,
        status=MILESTONE_PENDING,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def update_launch_milestone(
    db: Session,
    milestone_id: int,
    user: models.User,
    status: Optional[str] = None,
    actual_cost: Optional[float] = None,
    completed_date: Optional[str] = None,
) -> models.LaunchMilestone:
    """Updates progress or actual costs of a milestone."""
    m = db.query(models.LaunchMilestone).filter_by(id=milestone_id).first()
    if not m or m.workspace.user_id != user.id:
        raise PermissionError("Access denied to milestone")

    if status:
        m.status = status
    if actual_cost is not None:
        m.actual_cost = actual_cost
    if completed_date:
        m.completed_date = completed_date
    elif status == MILESTONE_COMPLETED and not m.completed_date:
        m.completed_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    db.commit()
    db.refresh(m)
    return m


def record_actual_period(
    db: Session,
    workspace_id: int,
    user: models.User,
    period_label: str,
    period_order: int,
    actual_revenue: float = 0.0,
    transactions_count: Optional[int] = None,
    average_ticket_size: Optional[float] = None,
    actual_capex: float = 0.0,
    actual_opex_salaries: float = 0.0,
    actual_opex_rent: float = 0.0,
    actual_opex_utilities: float = 0.0,
    actual_opex_marketing: float = 0.0,
    actual_opex_cogs: float = 0.0,
    actual_opex_other: float = 0.0,
    closing_cash_balance: Optional[float] = None,
    notes: Optional[str] = None,
) -> models.LaunchActualPeriod:
    """Records empirical operational actuals for a period with calculated OPEX and net cashflow."""
    ws = db.query(models.LaunchWorkspace).filter_by(id=workspace_id).first()
    if not ws or ws.user_id != user.id:
        raise PermissionError("Access denied to launch workspace")

    # If transactions and revenue given but no average ticket size, derive it cleanly
    aov = average_ticket_size
    if aov is None and transactions_count and transactions_count > 0 and actual_revenue > 0:
        aov = round(actual_revenue / transactions_count, 2)

    total_opex = round(
        float(actual_opex_salaries)
        + float(actual_opex_rent)
        + float(actual_opex_utilities)
        + float(actual_opex_marketing)
        + float(actual_opex_cogs)
        + float(actual_opex_other),
        2,
    )
    net_cf = round(float(actual_revenue) - float(actual_capex) - total_opex, 2)

    # Check if period already exists; if so, update; otherwise create
    existing = (
        db.query(models.LaunchActualPeriod)
        .filter_by(workspace_id=ws.id, period_order=period_order)
        .first()
    )
    if existing:
        existing.period_label = period_label
        existing.actual_revenue = actual_revenue
        existing.transactions_count = transactions_count
        existing.average_ticket_size = aov
        existing.actual_capex = actual_capex
        existing.actual_opex_salaries = actual_opex_salaries
        existing.actual_opex_rent = actual_opex_rent
        existing.actual_opex_utilities = actual_opex_utilities
        existing.actual_opex_marketing = actual_opex_marketing
        existing.actual_opex_cogs = actual_opex_cogs
        existing.actual_opex_other = actual_opex_other
        existing.total_actual_opex = total_opex
        existing.net_cashflow = net_cf
        existing.closing_cash_balance = closing_cash_balance
        existing.notes = notes
        existing.recorded_by = user.id
        period_record = existing
    else:
        period_record = models.LaunchActualPeriod(
            workspace_id=ws.id,
            period_label=period_label,
            period_order=period_order,
            actual_revenue=actual_revenue,
            transactions_count=transactions_count,
            average_ticket_size=aov,
            actual_capex=actual_capex,
            actual_opex_salaries=actual_opex_salaries,
            actual_opex_rent=actual_opex_rent,
            actual_opex_utilities=actual_opex_utilities,
            actual_opex_marketing=actual_opex_marketing,
            actual_opex_cogs=actual_opex_cogs,
            actual_opex_other=actual_opex_other,
            total_actual_opex=total_opex,
            net_cashflow=net_cf,
            closing_cash_balance=closing_cash_balance,
            notes=notes,
            recorded_by=user.id,
        )
        db.add(period_record)

    # Transition workspace status to LAUNCHED if actual revenue > 0
    if actual_revenue > 0 and ws.status == "PRE_LAUNCH":
        ws.status = "LAUNCHED"
        if not ws.actual_launch_date:
            ws.actual_launch_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    db.commit()
    db.refresh(period_record)
    return period_record


def calculate_period_variance(
    baseline_projection: Optional[Dict[str, Any]],
    actual_period: models.LaunchActualPeriod,
) -> Dict[str, Any]:
    """Calculates forecast vs actual variance with zero-denominator protection."""
    proj_rev = float(baseline_projection.get("projected_revenue", 0.0)) if baseline_projection else 0.0
    proj_opex = float(baseline_projection.get("projected_opex", 0.0)) if baseline_projection else 0.0
    proj_capex = float(baseline_projection.get("projected_capex", 0.0)) if baseline_projection else 0.0
    proj_net = float(baseline_projection.get("projected_net_cashflow", 0.0)) if baseline_projection else 0.0

    act_rev = float(actual_period.actual_revenue)
    act_opex = float(actual_period.total_actual_opex)
    act_capex = float(actual_period.actual_capex)
    act_net = float(actual_period.net_cashflow)

    rev_diff = round(act_rev - proj_rev, 2)
    opex_diff = round(act_opex - proj_opex, 2)
    net_diff = round(act_net - proj_net, 2)

    # Zero-denominator protection: never divide by zero
    rev_pct = round((rev_diff / proj_rev) * 100, 1) if proj_rev > 0 else None
    opex_pct = round((opex_diff / proj_opex) * 100, 1) if proj_opex > 0 else None

    # Alert evaluation
    if act_rev == 0 and act_opex == 0 and act_capex == 0:
        alert = ALERT_NO_DATA
        explanation_ar = "لا توجد مدخلات أداء فعلي مسجلة لهذه الفترة حتى الآن."
    else:
        worst_variance = max(
            abs(rev_pct) if rev_pct is not None else 0,
            abs(opex_pct) if opex_pct is not None else 0,
        )
        if worst_variance > 25.0:
            alert = ALERT_MATERIAL_VARIANCE
            explanation_ar = f"انحراف جوهري يتجاوز 25% (فارق الإيراد {rev_diff:,.0f} ر.س، فارق التكاليف {opex_diff:,.0f} ر.س). يوصى بإعادة التنبؤ فوراً."
        elif worst_variance > 10.0:
            alert = ALERT_WATCH
            explanation_ar = f"انحراف متوسط يستدعي المتابعة (فارق الإيراد {rev_diff:,.0f} ر.س)."
        else:
            alert = ALERT_NORMAL
            explanation_ar = "الأداء الفعلي يسير ضمن الحدود المتوقعة لخطة العمل (انحراف أقل من 10%)."

    return {
        "period_label": actual_period.period_label,
        "period_order": actual_period.period_order,
        "projected": {
            "revenue": proj_rev,
            "opex": proj_opex,
            "capex": proj_capex,
            "net_cashflow": proj_net,
        },
        "actual": {
            "revenue": act_rev,
            "opex": act_opex,
            "capex": act_capex,
            "net_cashflow": act_net,
            "transactions_count": actual_period.transactions_count,
            "average_ticket_size": actual_period.average_ticket_size,
        },
        "variance": {
            "revenue_diff": rev_diff,
            "revenue_pct": rev_pct,
            "opex_diff": opex_diff,
            "opex_pct": opex_pct,
            "net_diff": net_diff,
        },
        "alert": alert,
        "explanation_ar": explanation_ar,
    }


def evaluate_workspace_variances(
    ws: models.LaunchWorkspace,
) -> Dict[str, Any]:
    """Generates complete variance report comparing all recorded actuals against frozen baseline."""
    snapshot = ws.baseline_snapshots[0] if ws.baseline_snapshots else None
    proj_map = {}
    if snapshot and snapshot.monthly_projections:
        for p in snapshot.monthly_projections:
            proj_map[p.get("month")] = p

    period_variances = []
    total_act_rev = 0.0
    total_proj_rev = 0.0
    total_act_opex = 0.0
    total_proj_opex = 0.0

    for act in ws.actual_periods:
        baseline_p = proj_map.get(act.period_order)
        var_res = calculate_period_variance(baseline_p, act)
        period_variances.append(var_res)

        total_act_rev += float(act.actual_revenue)
        total_act_opex += float(act.total_actual_opex)
        if baseline_p:
            total_proj_rev += float(baseline_p.get("projected_revenue", 0.0))
            total_proj_opex += float(baseline_p.get("projected_opex", 0.0))

    cum_rev_diff = round(total_act_rev - total_proj_rev, 2)
    cum_opex_diff = round(total_act_opex - total_proj_opex, 2)
    cum_rev_pct = round((cum_rev_diff / total_proj_rev) * 100, 1) if total_proj_rev > 0 else None
    cum_opex_pct = round((cum_opex_diff / total_proj_opex) * 100, 1) if total_proj_opex > 0 else None

    # Cumulative health alert
    if not ws.actual_periods:
        overall_health = "PENDING_ACTUALS"
        summary_ar = "المشروع في مرحلة ما قبل الإطلاق / لم يتم إدخال بيانات فعلية بعد."
    else:
        worst_cum = max(
            abs(cum_rev_pct) if cum_rev_pct is not None else 0,
            abs(cum_opex_pct) if cum_opex_pct is not None else 0,
        )
        if worst_cum > 25.0:
            overall_health = ALERT_MATERIAL_VARIANCE
            summary_ar = f"تنبيه: انحراف تراكمي جوهري يتجاوز 25% مقارنة بالدراسة الأصلية. يلزم إجراء إعادة تنبؤ وضبط المصاريف."
        elif worst_cum > 10.0:
            overall_health = ALERT_WATCH
            summary_ar = "انحراف تراكمي معتدل (بين 10% و 25%). الأداء قيد المراقبة."
        else:
            overall_health = ALERT_NORMAL
            summary_ar = "الأداء الميداني الفعلي متطابق ومستقر مع تقديرات دراسة الجدوى الأساسية."

    return {
        "overall_health": overall_health,
        "summary_ar": summary_ar,
        "cumulative": {
            "total_actual_revenue": total_act_rev,
            "total_projected_revenue": total_proj_rev,
            "revenue_difference": cum_rev_diff,
            "revenue_difference_pct": cum_rev_pct,
            "total_actual_opex": total_act_opex,
            "total_projected_opex": total_proj_opex,
            "opex_difference": cum_opex_diff,
            "opex_difference_pct": cum_opex_pct,
        },
        "period_variances": period_variances,
    }


def generate_reforecast(
    db: Session,
    workspace_id: int,
    user: models.User,
    reforecast_title: str,
    adjustment_rationale: str,
    growth_rate_adjustment_pct: float = 0.0,
    opex_adjustment_pct: float = 0.0,
) -> models.LaunchReforecast:
    """Generates an updated forward projection (v1, v2...) based on actual historical burn rate and growth."""
    ws = db.query(models.LaunchWorkspace).filter_by(id=workspace_id).first()
    if not ws or ws.user_id != user.id:
        raise PermissionError("Access denied to launch workspace")

    snapshot = ws.baseline_snapshots[0] if ws.baseline_snapshots else None
    if not snapshot:
        raise ValueError("لا يمكن إعادة التنبؤ دون وجود نسخة خط أساس مجمدة (Baseline Snapshot)")

    actual_count = len(ws.actual_periods)
    latest_actual = ws.actual_periods[-1] if ws.actual_periods else None

    # Calculate historical monthly burn rate from actuals
    monthly_burn = 0.0
    latest_cash = float(snapshot.total_investment)
    if latest_actual and latest_actual.closing_cash_balance is not None:
        latest_cash = float(latest_actual.closing_cash_balance)

    if ws.actual_periods:
        negative_cfs = [abs(p.net_cashflow) for p in ws.actual_periods if p.net_cashflow < 0]
        if negative_cfs:
            monthly_burn = round(sum(negative_cfs) / len(negative_cfs), 2)
        else:
            monthly_burn = round(sum(p.total_actual_opex for p in ws.actual_periods) / len(ws.actual_periods), 2)

    # Runway calculation
    runway_months = None
    if monthly_burn > 0 and latest_cash > 0:
        runway_months = round(latest_cash / monthly_burn, 1)

    # Generate forward 12-month reforecast projections
    rev_multiplier = 1.0 + (growth_rate_adjustment_pct / 100.0)
    opex_multiplier = 1.0 + (opex_adjustment_pct / 100.0)

    reforecast_months = []
    break_even_month = None
    cum_cash = latest_cash

    for m in range(1, 13):
        # Base on original snapshot month projections, or extrapolating from last actual
        base_rev = 50000.0
        base_opex = 25000.0
        if snapshot.monthly_projections and len(snapshot.monthly_projections) >= m:
            base_rev = float(snapshot.monthly_projections[m - 1].get("projected_revenue", base_rev))
            base_opex = float(snapshot.monthly_projections[m - 1].get("projected_opex", base_opex))

        adj_rev = round(base_rev * rev_multiplier, 2)
        adj_opex = round(base_opex * opex_multiplier, 2)
        net_cf = round(adj_rev - adj_opex, 2)
        cum_cash = round(cum_cash + net_cf, 2)

        if net_cf > 0 and break_even_month is None:
            break_even_month = m

        reforecast_months.append({
            "month": m,
            "period_label": f"M{m:02d}",
            "reforecast_revenue": adj_rev,
            "reforecast_opex": adj_opex,
            "reforecast_net_cashflow": net_cf,
            "projected_closing_cash": cum_cash,
        })

    next_version = len(ws.reforecasts) + 1
    reforecast = models.LaunchReforecast(
        workspace_id=ws.id,
        version_number=next_version,
        reforecast_title=reforecast_title,
        adjustment_rationale=adjustment_rationale,
        growth_rate_adjustment_pct=growth_rate_adjustment_pct,
        opex_adjustment_pct=opex_adjustment_pct,
        monthly_burn_rate=monthly_burn,
        remaining_runway_months=runway_months,
        revised_break_even_month=break_even_month,
        reforecast_payload={
            "created_at": datetime.now(timezone.utc).isoformat(),
            "actual_periods_included": actual_count,
            "latest_cash_balance": latest_cash,
            "monthly_projections": reforecast_months,
        },
    )
    db.add(reforecast)
    db.commit()
    db.refresh(reforecast)
    return reforecast

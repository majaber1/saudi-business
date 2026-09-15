"""
V2 Standalone Consulting-Grade Feasibility Report Generator.

Reads from V2 StudyState and produces a multi-page professional PDF or DOCX.
No browser artifacts, no chat history, no workspace UI.

Sections:
1. Cover
2. Executive Decision Summary
3. Investment Snapshot
4. Business Profile
5. Market Analysis
6. Customer / Demand Analysis
7. Competitor Analysis
8. Business / Operating Model
9. Financial Model
10. Low / Base / High Scenarios
11. Sensitivity Analysis
12. Risk Analysis
13. Decision Conditions
14. Evidence Quality
15. Unknowns / Gaps
16. Final Recommendation
17. 30 / 60 / 90 Day Actions
18. Evidence & Source Register
19. Methodology / Assumptions
"""
from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any

try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    def _shape_ar(text: str) -> str:
        try:
            return get_display(arabic_reshaper.reshape(text))
        except Exception:
            return text
except Exception:
    def _shape_ar(text: str) -> str:
        return text


_ARABIC_FONTS_REGISTERED = False


def _register_arabic_fonts():
    global _ARABIC_FONTS_REGISTERED
    if _ARABIC_FONTS_REGISTERED:
        return
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        pdfmetrics.registerFont(TTFont("FreeSerif", "/usr/share/fonts/truetype/freefont/FreeSerif.ttf"))
        pdfmetrics.registerFont(TTFont("FreeSerifBold", "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf"))
        _ARABIC_FONTS_REGISTERED = True
    except Exception:
        pass


def _font(locale: str, bold: bool = False) -> str:
    if locale == "ar" and _ARABIC_FONTS_REGISTERED:
        return "FreeSerifBold" if bold else "FreeSerif"
    return "Helvetica-Bold" if bold else "Helvetica"


def _dir(text: str, locale: str) -> str:
    return _shape_ar(text) if locale == "ar" else text


def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return format(value, ",.2f")
    return str(value)


def _dedup_claims(claims: list[dict]) -> list[dict]:
    seen: set[str] = set()
    result = []
    for c in claims or []:
        stmt = (c.get("statement") or "").strip().lower()[:200]
        if stmt and stmt in seen:
            continue
        if stmt:
            seen.add(stmt)
        result.append(c)
    return result


def _trust_label(fr: dict) -> str:
    if not fr:
        return "NOT_INVESTMENT_GRADE"
    if fr.get("gate_status") == "BLOCKED":
        return "NOT_INVESTMENT_GRADE"
    npv = fr.get("npv")
    irr = fr.get("irr")
    if irr is not None and isinstance(irr, (int, float)) and irr > 2.0:
        return "UNVERIFIED_PROJECTION"
    roi = fr.get("roi")
    if roi is not None and isinstance(roi, (int, float)) and roi > 500:
        return "UNVERIFIED_PROJECTION"
    has_low_conf = False
    extract_notes = fr.get("extract_notes") or []
    warnings = fr.get("warnings") or []
    if any("default" in str(n).lower() for n in extract_notes):
        has_low_conf = True
    if any("unavailable" in str(w).lower() for w in warnings):
        has_low_conf = True
    if has_low_conf:
        return "PARTIAL"
    return "SYSTEM_ESTIMATE"


def _classify_evidence(claims: list[dict]) -> dict:
    relevant = []
    context = []
    low_relevance = []
    for c in claims:
        stmt = (c.get("statement") or "").lower()
        src = (c.get("source_type") or "").lower()
        if any(k in stmt for k in ["competitor", "crm", "saas", "pricing", "cac", "churn",
                                     "retention", "cloud", "api", "team", "salary", "pdpl",
                                     "licensing", "saudization", "customer"]):
            relevant.append(c)
        elif any(k in stmt for k in ["gdp", "inflation", "cpi", "population", "vision 2030",
                                       "digital transformation", "sme"]):
            context.append(c)
        else:
            low_relevance.append(c)
    return {"relevant": relevant, "context": context, "low_relevance": low_relevance}


LABELS = {
    "en": {
        "report_title": "Feasibility Study Report",
        "brand": "Saudi Business",
        "subtitle": "AI Business Operating System",
        "exec_summary": "1. Executive Decision Summary",
        "investment_snapshot": "2. Investment Snapshot",
        "business_profile": "3. Business Profile",
        "market_analysis": "4. Market Analysis",
        "customer_demand": "5. Customer & Demand Analysis",
        "competitor_analysis": "6. Competitor Analysis",
        "operating_model": "7. Business & Operating Model",
        "financial_model": "8. Financial Model",
        "scenarios": "9. Low / Base / High Scenarios",
        "sensitivity": "10. Sensitivity Analysis",
        "risk": "11. Risk Analysis",
        "conditions": "12. Decision Conditions",
        "evidence_quality": "13. Evidence Quality Assessment",
        "unknowns": "14. Unknowns & Gaps",
        "recommendation": "15. Final Recommendation",
        "action_plan": "16. 30 / 60 / 90 Day Action Plan",
        "evidence_register": "17. Evidence & Source Register",
        "assumptions_section": "18. Key Assumptions Register",
        "methodology": "19. Methodology & Disclaimer",
        "disclaimer": (
            "This report is generated by the Saudi Business AI platform as an assistive tool. "
            "It does not constitute legal, financial, or tax advice. All projections are system estimates "
            "and require independent professional review before investment decisions."
        ),
        "generated_on": "Generated on",
        "archetype": "Business Type",
        "sector": "Sector",
        "stage": "Stage",
        "goal": "Decision Goal",
        "investment": "Investment",
        "source": "Source",
        "confidence": "Confidence",
        "low": "Low",
        "base": "Base",
        "high": "High",
        "npv": "Net Present Value (NPV)",
        "irr": "Internal Rate of Return (IRR)",
        "payback": "Payback Period",
        "capex": "Initial Investment (CAPEX)",
        "revenue_y1": "Revenue Year 1",
        "opex_y1": "Operating Cost Year 1",
        "optimistic": "Optimistic (+20%)",
        "base_scenario": "Base Case",
        "conservative": "Conservative (-20%)",
        "trust_warnings": "Trust & Validation Warnings",
        "verdict": "Verdict",
        "rationale": "Rationale",
        "no_data": "No data available for this section.",
        "evidence_class": "Evidence Class",
        "assumption_key": "Assumption",
        "assumption_value": "Value",
        "gate_blocked": "FINANCIAL GATE: Analysis blocked due to missing material inputs. Not investment-grade.",
        "page": "Page",
        "trust_status": "Report Trust Status",
        "report_status_investment": "INVESTMENT-GRADE",
        "report_status_partial": "PARTIAL",
        "report_status_not_investment": "NOT INVESTMENT-GRADE",
    },
    "ar": {
        "report_title": "تقرير دراسة الجدوى",
        "brand": "سعودي بزنس",
        "subtitle": "نظام أعمال ذكاء اصطناعي",
        "exec_summary": "1. الملخص التنفيذي",
        "investment_snapshot": "2. لمحة الاستثمار",
        "business_profile": "3. الملف التعريفي",
        "market_analysis": "4. تحليل السوق",
        "customer_demand": "5. تحليل العملاء والطلب",
        "competitor_analysis": "6. تحليل المنافسين",
        "operating_model": "7. نموذج العمل",
        "financial_model": "8. النموذج المالي",
        "scenarios": "9. سيناريوهات",
        "sensitivity": "10. تحليل الحساسية",
        "risk": "11. تقييم المخاطر",
        "conditions": "12. شروط القرار",
        "evidence_quality": "13. جودة الأدلة",
        "unknowns": "14. المجهولات والفجوات",
        "recommendation": "15. التوصية النهائية",
        "action_plan": "16. خطة 30/60/90 يوم",
        "evidence_register": "17. سجل الأدلة والمصادر",
        "assumptions_section": "18. سجل الافتراضات",
        "methodology": "19. المنهجية وإخلاء المسؤولية",
        "disclaimer": (
            "هذا التقرير أداة مساعدة من منصة سعودي بزنس بالذكاء الاصطناعي. "
            "لا يُعدّ استشارة قانونية أو مالية أو ضريبية. جميع التوقعات تقديرات نظام "
            "وتتطلب مراجعة مهنية مستقلة قبل اتخاذ قرارات استثمارية."
        ),
        "generated_on": "تاريخ الإنشاء",
        "archetype": "نوع المشروع",
        "sector": "القطاع",
        "stage": "المرحلة",
        "goal": "هدف القرار",
        "investment": "الاستثمار",
        "source": "المصدر",
        "confidence": "الثقة",
        "low": "أدنى",
        "base": "أساسي",
        "high": "أعلى",
        "npv": "صافي القيمة الحالية",
        "irr": "معدل العائد الداخلي",
        "payback": "فترة الاسترداد",
        "capex": "الاستثمار الأولي",
        "revenue_y1": "إيراد السنة الأولى",
        "opex_y1": "تكلفة التشغيل",
        "optimistic": "متفائل (+20%)",
        "base_scenario": "الحالة الأساسية",
        "conservative": "متحفظ (-20%)",
        "trust_warnings": "تحذيرات الثقة",
        "verdict": "الحكم",
        "rationale": "المبررات",
        "no_data": "لا تتوفر بيانات لهذا القسم.",
        "evidence_class": "تصنيف الدليل",
        "assumption_key": "الافتراض",
        "assumption_value": "القيمة",
        "gate_blocked": "بوابة مالية: التحليل محجوب بسبب مدخلات جوهرية ناقصة.",
        "page": "صفحة",
        "trust_status": "مستوى ثقة التقرير",
        "report_status_investment": "بدرجة استثمارية",
        "report_status_partial": "جزئي",
        "report_status_not_investment": "غير بدرجة استثمارية",
    },
}


def build_v2_report_context(state: dict) -> dict:
    profile = state.get("profile") or {}
    if not isinstance(profile, dict):
        profile = profile.model_dump() if hasattr(profile, "model_dump") else {}

    claims_raw = state.get("claims") or []
    claims = []
    for c in claims_raw:
        if isinstance(c, dict):
            claims.append(c)
        elif hasattr(c, "model_dump"):
            claims.append(c.model_dump())
        else:
            claims.append({"statement": str(c)})

    assumptions_raw = state.get("assumptions") or []
    assumptions = []
    for a in assumptions_raw:
        if isinstance(a, dict):
            assumptions.append(a)
        elif hasattr(a, "model_dump"):
            assumptions.append(a.model_dump())
        else:
            assumptions.append({"key": str(a)})

    fr = state.get("financial_results") or {}

    return {
        "archetype": profile.get("archetype", "unknown"),
        "sector": profile.get("sector", ""),
        "stage": profile.get("stage", ""),
        "decision_goal": profile.get("decision_goal", ""),
        "language": state.get("language", "en"),
        "claims": _dedup_claims(claims),
        "assumptions": assumptions,
        "financial_results": fr,
        "verdict": state.get("verdict"),
        "decision_rationale": state.get("decision_rationale"),
        "decision_conditions": state.get("decision_conditions") or [],
        "decision_risks": state.get("decision_risks") or [],
        "decision_safety": state.get("decision_safety"),
        "phase": state.get("phase", "DRAFT"),
        "study_id": state.get("study_id", ""),
        "project_id": state.get("project_id", ""),
    }


def generate_v2_pdf(ctx: dict, locale: str = "en") -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen import canvas

    _register_arabic_fonts()
    L = LABELS.get(locale, LABELS["en"])
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    margin_left = 20 * mm
    margin_right = width - 20 * mm
    page_num = [1]
    y = [height - 20 * mm]

    def _check_page(needed: float = 30 * mm):
        if y[0] < needed:
            _footer()
            c.showPage()
            page_num[0] += 1
            y[0] = height - 20 * mm

    def _footer():
        c.setFont(_font(locale), 7)
        c.setFillColor(HexColor("#666666"))
        footer_text = f"{L['brand']} | {L['page']} {page_num[0]}"
        if locale == "ar":
            c.drawRightString(margin_right, 10 * mm, _dir(footer_text, locale))
        else:
            c.drawString(margin_left, 10 * mm, footer_text)
        c.setFillColor(HexColor("#000000"))

    def _section_title(title: str):
        _check_page(40 * mm)
        y[0] -= 6 * mm
        c.setFont(_font(locale, bold=True), 13)
        c.setFillColor(HexColor("#1a365d"))
        if locale == "ar":
            c.drawRightString(margin_right, y[0], _dir(title, locale))
        else:
            c.drawString(margin_left, y[0], title)
        c.setFillColor(HexColor("#000000"))
        y[0] -= 2 * mm
        c.setStrokeColor(HexColor("#2b6cb0"))
        c.setLineWidth(0.5)
        c.line(margin_left, y[0], margin_right, y[0])
        c.setStrokeColor(HexColor("#000000"))
        y[0] -= 7 * mm

    def _text(text: str, size: int = 10, bold: bool = False, color: str = "#000000", indent: float = 0):
        _check_page()
        c.setFont(_font(locale, bold), size)
        c.setFillColor(HexColor(color))
        max_width = (margin_right - margin_left - indent)
        words = text.split()
        line = ""
        for word in words:
            test = (line + " " + word).strip()
            if c.stringWidth(test, _font(locale, bold), size) > max_width:
                if line:
                    _check_page()
                    if locale == "ar":
                        c.drawRightString(margin_right - indent, y[0], _dir(line, locale))
                    else:
                        c.drawString(margin_left + indent, y[0], line)
                    y[0] -= size * 0.45 * mm
                line = word
            else:
                line = test
        if line:
            _check_page()
            if locale == "ar":
                c.drawRightString(margin_right - indent, y[0], _dir(line, locale))
            else:
                c.drawString(margin_left + indent, y[0], line)
            y[0] -= size * 0.45 * mm
        c.setFillColor(HexColor("#000000"))
        y[0] -= 2 * mm

    def _field(label: str, value: str, indent: float = 0):
        _check_page()
        c.setFont(_font(locale, bold=True), 10)
        lbl = _dir(label + ": ", locale)
        val = _dir(_fmt(value), locale)
        if locale == "ar":
            c.drawRightString(margin_right - indent, y[0], lbl + val)
        else:
            c.drawString(margin_left + indent, y[0], lbl + val)
        y[0] -= 6 * mm

    def _bullet(text: str, size: int = 9, indent: float = 5):
        _text(f"• {text}", size=size, indent=indent * mm)

    fr = ctx.get("financial_results") or {}
    trust = _trust_label(fr)

    # === 0. COVER ===
    c.setFont(_font(locale, bold=True), 24)
    c.setFillColor(HexColor("#1a365d"))
    title = _dir(L["report_title"], locale)
    if locale == "ar":
        c.drawRightString(margin_right, y[0], title)
    else:
        c.drawString(margin_left, y[0], title)
    y[0] -= 12 * mm

    c.setFont(_font(locale), 14)
    c.setFillColor(HexColor("#4a5568"))
    brand = _dir(L["brand"] + " — " + L["subtitle"], locale)
    if locale == "ar":
        c.drawRightString(margin_right, y[0], brand)
    else:
        c.drawString(margin_left, y[0], brand)
    c.setFillColor(HexColor("#000000"))
    y[0] -= 10 * mm

    c.setStrokeColor(HexColor("#2b6cb0"))
    c.setLineWidth(1)
    c.line(margin_left, y[0], margin_right, y[0])
    c.setStrokeColor(HexColor("#000000"))
    y[0] -= 10 * mm

    _field(L["archetype"], ctx.get("archetype", "—"))
    _field(L["sector"], ctx.get("sector", "—"))
    _field(L["stage"], ctx.get("stage", "—"))
    _field(L["generated_on"], datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    _field("Study ID", ctx.get("study_id", "—"))

    y[0] -= 4 * mm
    trust_color = "#c53030" if "NOT" in trust else ("#b7791f" if trust == "PARTIAL" else "#2f855a")
    _text(f"{L['trust_status']}: {trust}", size=12, bold=True, color=trust_color)

    # === 1. EXECUTIVE DECISION SUMMARY ===
    _section_title(L["exec_summary"])
    verdict = ctx.get("verdict") or "PENDING"
    _field(L["verdict"], verdict)
    rationale = ctx.get("decision_rationale") or L["no_data"]
    _text(rationale, size=10)

    capex = fr.get("capex")
    npv = fr.get("npv")
    irr_d = fr.get("irr_display") or _fmt(fr.get("irr"))
    payback_d = fr.get("payback_display") or _fmt(fr.get("payback_months"))
    if capex is not None:
        _text(f"Investment: {_fmt(capex)} SAR | NPV: {_fmt(npv)} SAR | IRR: {irr_d} | Payback: {payback_d}",
              size=9, color="#4a5568")

    # === 2. INVESTMENT SNAPSHOT ===
    _section_title(L["investment_snapshot"])
    _field(L["capex"], f"{_fmt(capex)} SAR" if capex else "—")
    inv_assumption = None
    for a in ctx.get("assumptions") or []:
        if a.get("key") in ("initial_investment", "capex", "seed"):
            inv_assumption = a
            break
    if inv_assumption:
        _text(f"Source: {inv_assumption.get('source', 'Owner-specified')}", size=9, color="#4a5568", indent=5 * mm)
        _text(f"Confidence: {inv_assumption.get('confidence', '—')}", size=9, color="#4a5568", indent=5 * mm)
        alloc = inv_assumption.get("allocation")
        if alloc:
            _text(f"Allocation: {alloc}", size=9, indent=5 * mm)
        else:
            _text("Allocation: UNKNOWN — retained as lump-sum initial investment", size=9, color="#b7791f", indent=5 * mm)
    else:
        _text("No initial investment assumption found.", size=9, color="#c53030")

    # === 3. BUSINESS PROFILE ===
    _section_title(L["business_profile"])
    _field(L["archetype"], ctx.get("archetype", "—"))
    _field(L["sector"], ctx.get("sector", "—"))
    _field(L["stage"], ctx.get("stage", "—"))
    _field(L["goal"], ctx.get("decision_goal", "—"))

    # === 4. MARKET ANALYSIS ===
    _section_title(L["market_analysis"])
    claims = ctx.get("claims") or []
    classified = _classify_evidence(claims)
    market_claims = [c for c in classified["relevant"] + classified["context"]
                     if any(k in (c.get("statement") or "").lower()
                            for k in ["market", "billion", "million", "sar", "growth", "vision 2030",
                                       "digital transformation", "sme", "gdp"])]
    if market_claims:
        for mc in market_claims[:6]:
            _bullet(mc.get("statement", ""), size=9)
            _text(f"[{mc.get('source_type', '—')} | Confidence: {mc.get('confidence', '—')}]",
                  size=7, color="#718096", indent=8 * mm)
    else:
        _text(L["no_data"])

    # === 5. CUSTOMER & DEMAND ANALYSIS ===
    _section_title(L["customer_demand"])
    cust_claims = [c for c in classified["relevant"]
                   if any(k in (c.get("statement") or "").lower()
                          for k in ["customer", "pricing", "subscription", "freemium", "user", "demand",
                                     "penetration", "smb", "sme"])]
    if cust_claims:
        for cc in cust_claims[:5]:
            _bullet(cc.get("statement", ""), size=9)
    else:
        _text("No direct customer/demand evidence collected.", size=9, color="#b7791f")
    cust_assumptions = [a for a in ctx.get("assumptions") or []
                        if a.get("key") in ("target_customers", "pricing", "churn", "cac", "arr")]
    if cust_assumptions:
        y[0] -= 2 * mm
        _text("Derived customer economics:", size=9, bold=True)
        for ca in cust_assumptions:
            _text(f"  {ca.get('key', '').replace('_', ' ').title()}: {ca.get('value', '—')} "
                  f"[L:{ca.get('low')} / B:{ca.get('base')} / H:{ca.get('high')}]",
                  size=8, indent=5 * mm)

    # === 6. COMPETITOR ANALYSIS ===
    _section_title(L["competitor_analysis"])
    comp_claims = [c for c in classified["relevant"]
                   if any(k in (c.get("statement") or "").lower()
                          for k in ["competitor", "salesforce", "hubspot", "zoho", "dynamics",
                                     "qoyod", "foodics", "crm", "alternative"])]
    if comp_claims:
        for cc in comp_claims[:5]:
            _bullet(cc.get("statement", ""), size=9)
    else:
        _text("No competitor evidence collected.", size=9, color="#b7791f")

    # === 7. BUSINESS & OPERATING MODEL ===
    _section_title(L["operating_model"])
    _text("Revenue Model: B2B SaaS Subscription (monthly recurring)", size=10, bold=True)
    ops_claims = [c for c in classified["relevant"]
                  if any(k in (c.get("statement") or "").lower()
                         for k in ["cloud", "api", "team", "salary", "infrastructure",
                                    "aws", "gcp", "cost", "opex"])]
    if ops_claims:
        for oc in ops_claims[:4]:
            _bullet(oc.get("statement", ""), size=9)
    opex_a = None
    team_a = None
    for a in ctx.get("assumptions") or []:
        if a.get("key") == "opex_year1":
            opex_a = a
        if a.get("key") == "team_size_y1":
            team_a = a
    if opex_a:
        _text(f"OPEX Y1: {opex_a.get('value', '—')} SAR [{opex_a.get('source', '')}]",
              size=9, indent=5 * mm)
    if team_a:
        _text(f"Team: {team_a.get('value', '—')} [{team_a.get('source', '')}]",
              size=9, indent=5 * mm)

    # === 8. FINANCIAL MODEL ===
    _section_title(L["financial_model"])
    if not fr:
        _text(L["no_data"])
    elif fr.get("gate_status") == "BLOCKED":
        _text(L["gate_blocked"], size=11, bold=True, color="#c53030")
        missing = fr.get("missing_material_inputs", [])
        if missing:
            _text(f"Missing: {', '.join(missing)}", size=10, color="#c53030")
    else:
        _field(L["capex"], f"{_fmt(fr.get('capex'))} SAR")
        rev = fr.get("revenue_projections", {})
        if isinstance(rev, dict):
            for k, v in sorted(rev.items()):
                _field(f"Revenue {k.replace('_', ' ').title()}", f"{_fmt(v)} SAR")
        cost_proj = fr.get("cost_projections", {})
        if isinstance(cost_proj, dict):
            for k, v in sorted(cost_proj.items()):
                _field(f"OPEX {k.replace('_', ' ').title()}", f"{_fmt(v)} SAR")

        y[0] -= 3 * mm
        _field(L["npv"], f"{_fmt(fr.get('npv'))} SAR")
        _field(L["irr"], fr.get("irr_display") or _fmt(fr.get("irr")))
        _field(L["payback"], fr.get("payback_display") or _fmt(fr.get("payback_months")))

        proj_years = fr.get("projection_years", 3)
        _text(f"Projection horizon: {proj_years} years (primary decision)", size=8, color="#4a5568")

        extract_notes = fr.get("extract_notes") or []
        if extract_notes:
            y[0] -= 2 * mm
            _text("Extraction notes:", size=8, bold=True, color="#718096")
            for note in extract_notes[:5]:
                _text(f"  • {note}", size=7, color="#718096", indent=5 * mm)

    # === 9. SCENARIOS ===
    _section_title(L["scenarios"])
    scenarios = fr.get("scenarios", {})
    if scenarios:
        for label_key, data_key in [("optimistic", "optimistic"), ("base_scenario", "base"), ("conservative", "conservative")]:
            sc = scenarios.get(data_key, {})
            if sc:
                sc_npv = _fmt(sc.get("npv"))
                sc_irr = sc.get("irr_display") or _fmt(sc.get("irr"))
                _text(f"{L[label_key]}: NPV = {sc_npv} SAR, IRR = {sc_irr}", size=10, bold=True)
    else:
        _text(L["no_data"])

    # Low/Base/High from assumptions
    y[0] -= 3 * mm
    _text("Assumption-level scenario ranges:", size=9, bold=True)
    for a in ctx.get("assumptions") or []:
        low = a.get("low", "—")
        base_v = a.get("base", "—")
        high_v = a.get("high", "—")
        if low == base_v == high_v:
            continue
        label = a.get("key", "").replace("_", " ").title()
        _text(f"  {label}: Low={low} | Base={base_v} | High={high_v}", size=8, indent=5 * mm)

    # === 10. SENSITIVITY ANALYSIS ===
    _section_title(L["sensitivity"])
    _text("Key sensitivities (base-case NPV impact):", size=10, bold=True)
    base_npv = fr.get("npv")
    opt_npv = (scenarios.get("optimistic") or {}).get("npv")
    con_npv = (scenarios.get("conservative") or {}).get("npv")
    if base_npv is not None and opt_npv is not None and con_npv is not None:
        _text(f"  Revenue +20%: NPV shifts from {_fmt(base_npv)} to {_fmt(opt_npv)} SAR "
              f"(delta: {_fmt(opt_npv - base_npv)})", size=9, indent=5 * mm)
        _text(f"  Revenue -20%: NPV shifts from {_fmt(base_npv)} to {_fmt(con_npv)} SAR "
              f"(delta: {_fmt(con_npv - base_npv)})", size=9, indent=5 * mm)
        _text(f"  NPV range: {_fmt(con_npv)} to {_fmt(opt_npv)} SAR", size=9, bold=True, indent=5 * mm)
    else:
        _text("Insufficient data for sensitivity calculation.", size=9, color="#b7791f")

    # === 11. RISK ANALYSIS ===
    _section_title(L["risk"])
    risks = ctx.get("decision_risks") or []
    if not risks:
        _text(L["no_data"])
    else:
        for i, risk in enumerate(risks[:15], 1):
            if isinstance(risk, str):
                _text(f"{i}. {risk}", size=9)
            elif isinstance(risk, dict):
                cat = risk.get("category", "—")
                desc = risk.get("description", "—")
                sev = risk.get("severity", "")
                _text(f"{i}. [{cat}] {desc}" + (f" (Severity: {sev})" if sev else ""), size=9)
                mit = risk.get("mitigation")
                if mit:
                    _text(f"   Mitigation: {mit}", size=8, color="#4a5568", indent=8 * mm)

    # === 12. DECISION CONDITIONS ===
    _section_title(L["conditions"])
    conditions = ctx.get("decision_conditions") or []
    if conditions:
        for cond in conditions:
            _bullet(cond, size=9)
    else:
        _text("No conditions specified.", size=9)

    # === 13. EVIDENCE QUALITY ===
    _section_title(L["evidence_quality"])
    total = len(claims)
    official = sum(1 for c in claims if c.get("source_type") == "official")
    ai_est = sum(1 for c in claims if c.get("source_type") in ("ai_assumption", "ai_estimated"))
    user_in = sum(1 for c in claims if c.get("source_type") == "user_input")
    _text(f"Total evidence items: {total}", size=10)
    _text(f"  Official/research sources: {official}", size=9, indent=5 * mm)
    _text(f"  AI-estimated: {ai_est}", size=9, indent=5 * mm)
    _text(f"  User-provided: {user_in}", size=9, indent=5 * mm)
    _text(f"  Relevant: {len(classified['relevant'])} | Context: {len(classified['context'])} | Low-relevance: {len(classified['low_relevance'])}",
          size=9, indent=5 * mm)

    all_conf = [c.get("confidence") for c in claims if c.get("confidence") is not None]
    if all_conf:
        numeric_conf = [float(x) for x in all_conf if isinstance(x, (int, float))]
        if numeric_conf:
            avg_conf = sum(numeric_conf) / len(numeric_conf)
            _text(f"  Average confidence: {avg_conf:.2f}", size=9, indent=5 * mm)

    # === 14. UNKNOWNS & GAPS ===
    _section_title(L["unknowns"])
    gaps = []
    for a in ctx.get("assumptions") or []:
        if a.get("confidence") == "low":
            gaps.append(f"Low-confidence assumption: {a.get('key', '?').replace('_', ' ')} = {a.get('value', '?')}")
        if a.get("ai_estimated"):
            gaps.append(f"AI-estimated (needs validation): {a.get('key', '?').replace('_', ' ')}")
    extract_notes = fr.get("extract_notes") or []
    for note in extract_notes:
        if "default" in str(note).lower() or "missing" in str(note).lower():
            gaps.append(f"Financial extraction note: {note}")
    warnings = fr.get("warnings") or []
    for w in warnings:
        if "unavailable" in str(w).lower() or "estimated" in str(w).lower():
            gaps.append(f"Financial warning: {w}")
    seen_gaps = set()
    for g in gaps:
        norm = g.lower()[:100]
        if norm in seen_gaps:
            continue
        seen_gaps.add(norm)
        _bullet(g, size=9)
    if not gaps:
        _text("No critical gaps identified.", size=9)

    # === 15. FINAL RECOMMENDATION ===
    _section_title(L["recommendation"])
    _field(L["verdict"], verdict)
    _text(rationale, size=10)
    _text(f"Trust Status: {trust}", size=10, bold=True, color=trust_color)

    # === 16. 30/60/90 DAY ACTION PLAN ===
    _section_title(L["action_plan"])
    if verdict in ("DEFER", "GO_WITH_CONDITIONS"):
        _text("30 Days:", size=10, bold=True)
        _bullet("Conduct 15-20 customer discovery interviews with target Saudi SMEs", size=9)
        _bullet("Validate pricing willingness-to-pay (SAR 150-500 range)", size=9)
        _bullet("Assess competitive landscape through direct competitor demos", size=9)
        y[0] -= 2 * mm
        _text("60 Days:", size=10, bold=True)
        _bullet("Secure 3-5 letter-of-intent or pilot agreements", size=9)
        _bullet("Finalize MVP scope and technical architecture", size=9)
        _bullet("Begin PDPL compliance framework implementation", size=9)
        y[0] -= 2 * mm
        _text("90 Days:", size=10, bold=True)
        _bullet("Launch closed-beta with pilot customers", size=9)
        _bullet("Validate unit economics (CAC, activation, early retention)", size=9)
        _bullet("Update financial model with real data for final go/no-go", size=9)
    elif verdict == "GO":
        _text("30 Days: Finalize team hiring and begin MVP development", size=10)
        _text("60 Days: Launch beta, begin customer onboarding", size=10)
        _text("90 Days: Reach first revenue milestone, validate metrics", size=10)
    elif verdict == "NO_GO":
        _text("Recommendation: Do not proceed with current business model.", size=10)
        _text("Consider: Pivot strategy, alternative market segment, or partnership model.", size=10)
    else:
        _text("Action plan pending final verdict.", size=9)

    # === 17. EVIDENCE & SOURCE REGISTER ===
    _section_title(L["evidence_register"])
    if not claims:
        _text(L["no_data"])
    else:
        for i, claim in enumerate(claims[:30], 1):
            stmt = claim.get("statement", "")
            src = claim.get("source_type", "unknown")
            conf = claim.get("confidence", "—")
            url = claim.get("source_url", "")
            origin = claim.get("origin", "—")
            _text(f"{i}. {stmt}", size=8)
            detail = f"   Class: {src} | Confidence: {conf} | Origin: {origin}"
            if url:
                detail += f" | URL: {url}"
            _text(detail, size=7, color="#4a5568", indent=5 * mm)

    # === 18. KEY ASSUMPTIONS REGISTER ===
    _section_title(L["assumptions_section"])
    assumptions = ctx.get("assumptions") or []
    if not assumptions:
        _text(L["no_data"])
    else:
        for a in assumptions:
            key = a.get("key", "—")
            value = a.get("value", "—")
            source = a.get("source", "—")
            conf = a.get("confidence", "—")
            low = a.get("low", "—")
            base_v = a.get("base", "—")
            high_val = a.get("high", "—")
            ai_est = a.get("ai_estimated", False)
            origin = a.get("origin", "—")

            label = key.replace("_", " ").title()
            ev_class = "USER_CONFIRMED" if origin == "user" else "SYSTEM_ESTIMATE"
            _text(f"{label}: {value}", size=10, bold=True)
            _text(f"   Source: {source}", size=8, color="#4a5568", indent=5 * mm)
            _text(f"   Evidence class: {ev_class} | Confidence: {conf} | AI estimated: {ai_est}",
                  size=8, color="#4a5568", indent=5 * mm)
            _text(f"   Low: {low} | Base: {base_v} | High: {high_val}",
                  size=8, color="#718096", indent=5 * mm)

    # === 19. METHODOLOGY & DISCLAIMER ===
    _section_title(L["methodology"])
    _text("Methodology:", size=10, bold=True)
    _text("This feasibility assessment uses a structured multi-phase analysis framework:", size=9)
    _bullet("Evidence collection from public sources, industry benchmarks, and regulatory databases", size=8)
    _bullet("Assumption generation with Low/Base/High ranges and confidence scoring", size=8)
    _bullet("Deterministic financial modeling (DCF/NPV/IRR) with scenario analysis", size=8)
    _bullet("Risk assessment across market, regulatory, operational, financial, and external categories", size=8)
    _bullet("Decision gate validation with financial trust gates and evidence sufficiency checks", size=8)
    y[0] -= 3 * mm
    _text("Limitations:", size=10, bold=True)
    _bullet("All AI-estimated assumptions require independent validation", size=8)
    _bullet("Financial projections are based on benchmarks and may not reflect actual performance", size=8)
    _bullet("Regulatory requirements should be confirmed with qualified legal counsel", size=8)
    y[0] -= 3 * mm
    _text(L["disclaimer"], size=8, color="#718096")
    _text(f"{L['brand']} — {L['subtitle']}", size=8, color="#718096")

    _footer()
    c.showPage()
    c.save()
    return buf.getvalue()


def generate_v2_docx(ctx: dict, locale: str = "en") -> bytes:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt, RGBColor

    L = LABELS.get(locale, LABELS["en"])
    align = WD_ALIGN_PARAGRAPH.RIGHT if locale == "ar" else WD_ALIGN_PARAGRAPH.LEFT
    doc = Document()

    def _para(text: str, bold: bool = False, size: int = 11, color: tuple = None):
        p = doc.add_paragraph()
        p.alignment = align
        run = p.add_run(text)
        run.bold = bold
        run.font.size = Pt(size)
        if color:
            run.font.color.rgb = RGBColor(*color)
        return p

    def _section(title: str):
        _para("")
        return _para(title, bold=True, size=14, color=(26, 54, 93))

    fr = ctx.get("financial_results") or {}
    trust = _trust_label(fr)
    claims = ctx.get("claims") or []
    classified = _classify_evidence(claims)

    # Cover
    _para(L["report_title"], bold=True, size=24, color=(26, 54, 93))
    _para(L["brand"] + " — " + L["subtitle"], size=14, color=(74, 85, 104))
    _para("")
    _para(f"{L['archetype']}: {ctx.get('archetype', '—')}")
    _para(f"{L['sector']}: {ctx.get('sector', '—')}")
    _para(f"{L['generated_on']}: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
    _para(f"Study ID: {ctx.get('study_id', '—')}")
    trust_color = (197, 48, 48) if "NOT" in trust else ((183, 121, 31) if trust == "PARTIAL" else (47, 133, 90))
    _para(f"{L['trust_status']}: {trust}", bold=True, size=12, color=trust_color)

    # 1. Executive Summary
    _section(L["exec_summary"])
    verdict = ctx.get("verdict") or "PENDING"
    _para(f"{L['verdict']}: {verdict}", bold=True)
    _para(ctx.get("decision_rationale") or L["no_data"])

    # 2. Investment Snapshot
    _section(L["investment_snapshot"])
    _para(f"{L['capex']}: {_fmt(fr.get('capex'))} SAR")
    inv_a = next((a for a in ctx.get("assumptions") or []
                  if a.get("key") in ("initial_investment", "capex")), None)
    if inv_a:
        _para(f"Source: {inv_a.get('source', 'Owner-specified')}", size=9, color=(74, 85, 104))
        _para("Allocation: UNKNOWN — retained as lump-sum", size=9, color=(183, 121, 31))

    # 3. Business Profile
    _section(L["business_profile"])
    _para(f"{L['archetype']}: {ctx.get('archetype', '—')}")
    _para(f"{L['sector']}: {ctx.get('sector', '—')}")
    _para(f"{L['stage']}: {ctx.get('stage', '—')}")
    _para(f"{L['goal']}: {ctx.get('decision_goal', '—')}")

    # 4. Market Analysis
    _section(L["market_analysis"])
    market_claims = [c for c in classified["relevant"] + classified["context"]
                     if any(k in (c.get("statement") or "").lower()
                            for k in ["market", "billion", "million", "vision 2030", "sme"])]
    for mc in market_claims[:6]:
        _para(f"• {mc.get('statement', '')}", size=9)

    # 5. Customer & Demand
    _section(L["customer_demand"])
    cust_claims = [c for c in classified["relevant"]
                   if any(k in (c.get("statement") or "").lower()
                          for k in ["customer", "pricing", "subscription", "user"])]
    for cc in cust_claims[:5]:
        _para(f"• {cc.get('statement', '')}", size=9)
    for a in ctx.get("assumptions") or []:
        if a.get("key") in ("target_customers", "pricing", "churn", "cac"):
            _para(f"  {a['key'].replace('_', ' ').title()}: {a.get('value')} "
                  f"[L:{a.get('low')}/B:{a.get('base')}/H:{a.get('high')}]", size=8, color=(74, 85, 104))

    # 6. Competitor Analysis
    _section(L["competitor_analysis"])
    comp_claims = [c for c in classified["relevant"]
                   if any(k in (c.get("statement") or "").lower()
                          for k in ["competitor", "salesforce", "hubspot", "zoho", "crm"])]
    for cc in comp_claims[:5]:
        _para(f"• {cc.get('statement', '')}", size=9)

    # 7. Operating Model
    _section(L["operating_model"])
    _para("Revenue Model: B2B SaaS Subscription", bold=True, size=10)
    for a in ctx.get("assumptions") or []:
        if a.get("key") in ("opex_year1", "team_size_y1"):
            _para(f"  {a['key'].replace('_', ' ').title()}: {a.get('value')} [{a.get('source', '')}]", size=9)

    # 8. Financial Model
    _section(L["financial_model"])
    if fr.get("gate_status") == "BLOCKED":
        _para(L["gate_blocked"], bold=True, size=11, color=(197, 48, 48))
    elif fr:
        _para(f"{L['capex']}: {_fmt(fr.get('capex'))} SAR")
        _para(f"{L['npv']}: {_fmt(fr.get('npv'))} SAR")
        _para(f"{L['irr']}: {fr.get('irr_display') or _fmt(fr.get('irr'))}")
        _para(f"{L['payback']}: {fr.get('payback_display') or _fmt(fr.get('payback_months'))}")
        _para(f"Projection horizon: {fr.get('projection_years', 3)} years", size=9, color=(74, 85, 104))

    # 9. Scenarios
    _section(L["scenarios"])
    scenarios = fr.get("scenarios", {})
    for lk, dk in [("optimistic", "optimistic"), ("base_scenario", "base"), ("conservative", "conservative")]:
        sc = scenarios.get(dk, {})
        if sc:
            _para(f"{L[lk]}: NPV={_fmt(sc.get('npv'))} SAR, IRR={sc.get('irr_display') or _fmt(sc.get('irr'))}")

    # 10. Sensitivity
    _section(L["sensitivity"])
    base_npv = fr.get("npv")
    opt_npv = (scenarios.get("optimistic") or {}).get("npv")
    con_npv = (scenarios.get("conservative") or {}).get("npv")
    if base_npv is not None and opt_npv is not None:
        _para(f"NPV range: {_fmt(con_npv)} to {_fmt(opt_npv)} SAR", size=10)

    # 11. Risk
    _section(L["risk"])
    for i, risk in enumerate(ctx.get("decision_risks") or [], 1):
        if isinstance(risk, str):
            _para(f"{i}. {risk}", size=9)
        elif isinstance(risk, dict):
            _para(f"{i}. [{risk.get('category', '—')}] {risk.get('description', '—')}", size=9)

    # 12. Conditions
    _section(L["conditions"])
    for cond in ctx.get("decision_conditions") or []:
        _para(f"• {cond}", size=9)

    # 13. Evidence Quality
    _section(L["evidence_quality"])
    _para(f"Total: {len(claims)} | Official: {sum(1 for c in claims if c.get('source_type') == 'official')}", size=10)
    _para(f"Relevant: {len(classified['relevant'])} | Context: {len(classified['context'])}", size=9)

    # 14. Unknowns & Gaps
    _section(L["unknowns"])
    for a in ctx.get("assumptions") or []:
        if a.get("confidence") == "low":
            _para(f"• Low confidence: {a.get('key', '?').replace('_', ' ')}", size=9, color=(183, 121, 31))

    # 15. Recommendation
    _section(L["recommendation"])
    _para(f"{L['verdict']}: {verdict}", bold=True, size=12)
    _para(f"Trust Status: {trust}", bold=True, color=trust_color)

    # 16. Action Plan
    _section(L["action_plan"])
    if verdict in ("DEFER", "GO_WITH_CONDITIONS"):
        _para("30 Days: Customer discovery + pricing validation", size=10)
        _para("60 Days: Pilot agreements + MVP scope + PDPL compliance", size=10)
        _para("90 Days: Closed-beta launch + unit economics validation", size=10)

    # 17. Evidence Register
    _section(L["evidence_register"])
    for i, claim in enumerate(claims[:30], 1):
        _para(f"{i}. {claim.get('statement', '')}", size=8)
        _para(f"   [{claim.get('source_type', '—')} | {claim.get('confidence', '—')} | {claim.get('origin', '—')}]",
              size=7, color=(74, 85, 104))

    # 18. Assumptions Register
    _section(L["assumptions_section"])
    for a in ctx.get("assumptions") or []:
        ev_class = "USER_CONFIRMED" if a.get("origin") == "user" else "SYSTEM_ESTIMATE"
        _para(f"{a.get('key', '—').replace('_', ' ').title()}: {a.get('value', '—')}", bold=True, size=10)
        _para(f"  Source: {a.get('source', '—')} | Class: {ev_class} | "
              f"Confidence: {a.get('confidence', '—')} | "
              f"L:{a.get('low')} / B:{a.get('base')} / H:{a.get('high')}", size=8, color=(74, 85, 104))

    # 19. Methodology
    _section(L["methodology"])
    _para(L["disclaimer"], size=8, color=(113, 128, 150))

    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()

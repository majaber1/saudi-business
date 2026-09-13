"""Deterministic business-archetype intelligence for assumption collection.

NOT an LLM decision. Ensures F&B / manufacturing / SaaS collect the right
required assumptions (Product Validation Sprint gap #1).
"""
from __future__ import annotations

from typing import Any

from ai_engine.archetypes.classifier import (
    ARCHETYPE_LABELS,
    SUPPORTED_ARCHETYPES,
    classify_archetype,
    normalize_archetype,
)
from ai_engine.archetypes.schemas import ASSUMPTION_SCHEMAS, get_assumption_schema

HARDENING_ARCHETYPES = (
    "fnb",
    "retail",
    "industrial",
    "services",
    "saas_digital",
    "marketplace",
    "real_estate",
    "data_center",
    "healthcare",
    "education",
    "other",
)

CRITICAL_ASSUMPTION_KEYS: dict[str, frozenset[str]] = {
    "fnb": frozenset({"avg_ticket", "daily_covers", "rent_monthly", "food_cost_pct", "seats_capacity"}),
    "retail": frozenset({"avg_ticket", "monthly_transactions", "rent_or_lease", "gross_margin"}),
    "industrial": frozenset(
        {"production_capacity", "utilization", "capex_machinery", "selling_price", "raw_material_cost"}
    ),
    "saas_digital": frozenset({"pricing", "cac", "churn", "arr", "target_customers"}),
    "services": frozenset(
        {"consultants_headcount", "utilization_rate", "billing_rate", "active_contracts"}
    ),
    "marketplace": frozenset({"take_rate", "monthly_trips", "drivers"}),
    "real_estate": frozenset({"land_cost", "construction_boq", "units", "selling_price"}),
    "data_center": frozenset({"mw_capacity", "capex_total", "year1_occupancy"}),
    "healthcare": frozenset({"avg_ticket", "daily_covers", "rent_monthly"}),
    "education": frozenset({"avg_ticket", "daily_covers", "rent_monthly"}),
    "other": frozenset({"year1_revenue", "initial_investment"}),
}

WHY_REQUIRED: dict[str, dict[str, str]] = {
    "avg_ticket": {
        "en": "Average ticket drives revenue capacity for location-based businesses.",
        "ar": "متوسط قيمة الفاتورة يحدد طاقة الإيراد للأعمال المعتمدة على الموقع.",
    },
    "daily_covers": {
        "en": "Daily covers link seating capacity to achievable revenue.",
        "ar": "الزبائن اليوميون يربطون سعة المقاعد بالإيراد القابل للتحقيق.",
    },
    "seats_capacity": {
        "en": "Seats/capacity set the physical upper bound for F&B demand.",
        "ar": "المقاعد / السعة تحدد الحد الأعلى للطلب في المطاعم والمقاهي.",
    },
    "rent_monthly": {
        "en": "Rent is usually the largest fixed cost and gates location economics.",
        "ar": "الإيجار عادة أكبر تكلفة ثابتة ويحدد اقتصاديات الموقع.",
    },
    "food_cost_pct": {
        "en": "Food cost % is the primary margin lever for F&B.",
        "ar": "نسبة تكلفة الطعام هي رافعة الهامش الأساسية للمطاعم والمقاهي.",
    },
    "labor_monthly": {
        "en": "Labor cost is a core F&B operating assumption.",
        "ar": "تكلفة العمالة افتراض تشغيلي أساسي للمطاعم والمقاهي.",
    },
    "production_capacity": {
        "en": "Capacity sets the upper bound of manufacturing revenue.",
        "ar": "الطاقة الإنتاجية تحدد الحد الأعلى لإيراد التصنيع.",
    },
    "utilization": {
        "en": "Utilization converts nameplate capacity into realistic output.",
        "ar": "نسبة التشغيل تحول الطاقة الاسمية إلى إنتاج واقعي.",
    },
    "capex_machinery": {
        "en": "Machinery CAPEX dominates industrial investment feasibility.",
        "ar": "النفقات الرأسمالية للآلات تهيمن على جدوى الاستثمار الصناعي.",
    },
    "selling_price": {
        "en": "Unit selling price anchors industrial unit economics.",
        "ar": "سعر بيع الوحدة يرسّخ اقتصاد الوحدة الصناعي.",
    },
    "raw_material_cost": {
        "en": "Raw material cost is the core supply-chain assumption.",
        "ar": "تكلفة المواد الخام هي افتراض سلسلة التوريد الأساسي.",
    },
    "pricing": {
        "en": "Subscription pricing is the core SaaS unit-economics input.",
        "ar": "تسعير الاشتراك هو مدخل اقتصاد الوحدة الأساسي لـ SaaS.",
    },
    "cac": {
        "en": "CAC determines whether growth is capital-efficient.",
        "ar": "تكلفة اكتساب العميل تحدد إن كان النمو كفؤاً رأسمالياً.",
    },
    "churn": {
        "en": "Churn controls whether recurring revenue compounds or leaks.",
        "ar": "التسرب يحدد إن كان الإيراد المتكرر يتراكم أو يتسرب.",
    },
    "arr": {
        "en": "ARR is the primary SaaS scale and valuation signal.",
        "ar": "الإيراد السنوي المتكرر هو مؤشر الحجم والتقييم الأساسي لـ SaaS.",
    },
    "target_customers": {
        "en": "Year-1 customer volume anchors ARR and CAC payback.",
        "ar": "حجم العملاء في السنة الأولى يحدد ARR وفترة استرداد CAC.",
    },
}


def classify_business_archetype(text: str) -> str:
    """Deterministic classifier with F&B before retail/services."""
    t = (text or "").lower()

    fnb_kw = (
        "coffee",
        "café",
        "cafe",
        "restaurant",
        "قهوة",
        "مقهى",
        "مطعم",
        "specialty coffee",
        "food truck",
        "bakery",
        "مخبز",
        "f&b",
        "fnb",
        "catering",
        "مأكولات",
        "مشروبات",
        "quick service",
        "qsr",
        "cloud kitchen",
        "مطبخ سحابي",
    )
    if any(k in t for k in fnb_kw):
        return "fnb"

    health_kw = ("clinic", "hospital", "healthcare", "dental", "عيادة", "مستشفى", "صحي", "طبي")
    if any(k in t for k in health_kw):
        return "healthcare"

    edu_kw = (
        "school",
        "training center",
        "academy",
        "education",
        "مدرسة",
        "تدريب",
        "أكاديمية",
        "تعليم",
    )
    if any(k in t for k in edu_kw):
        return "education"

    marketplace_kw = (
        "marketplace",
        "two-sided",
        "take rate",
        "ride-hailing",
        "uber",
        "careem",
        "منصة سوق",
        "سوق إلكتروني",
    )
    if any(k in t for k in marketplace_kw):
        return "marketplace"

    base = classify_archetype(text)
    return normalize_business_archetype(base, context_text=text)


def normalize_business_archetype(value: str | None, *, context_text: str | None = None) -> str:
    raw = (value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "fnb": "fnb",
        "food_beverage": "fnb",
        "food_and_beverage": "fnb",
        "restaurant": "fnb",
        "cafe": "fnb",
        "coffee": "fnb",
        "manufacturing": "industrial",
        "industrial_service": "services",
        "professional_service": "services",
        "professional_services": "services",
        "marketplace": "marketplace",
        "healthcare": "healthcare",
        "health": "healthcare",
        "education": "education",
        "saas": "saas_digital",
        "saas_digital": "saas_digital",
    }
    if raw in aliases:
        mapped = aliases[raw]
    else:
        mapped = normalize_archetype(raw)

    if mapped in {"services", "retail", "other"} and context_text:
        t = context_text.lower()
        if any(k in t for k in ("coffee", "café", "cafe", "restaurant", "قهوة", "مقهى", "مطعم")):
            return "fnb"
        if any(k in t for k in ("marketplace", "uber", "careem", "take rate")):
            return "marketplace"

    if mapped in HARDENING_ARCHETYPES:
        return mapped
    if mapped in SUPPORTED_ARCHETYPES:
        return mapped
    return "other"


def schema_archetype_for(business_archetype: str) -> str:
    arch = normalize_business_archetype(business_archetype)
    if arch in {"fnb", "healthcare", "education"}:
        return "fnb"
    if arch == "marketplace":
        return "services"
    known = set(ASSUMPTION_SCHEMAS.keys())
    return arch if arch in known else "other"


def required_assumptions_for(
    archetype: str,
    *,
    context_text: str | None = None,
) -> list[dict[str, Any]]:
    biz = normalize_business_archetype(archetype, context_text=context_text)
    schema_id = schema_archetype_for(biz)
    services_variant = "mobility" if biz == "marketplace" else None
    fields = get_assumption_schema(
        schema_id,
        context_text=context_text,
        services_variant=services_variant,
    )
    crit = CRITICAL_ASSUMPTION_KEYS.get(biz, frozenset())
    out: list[dict[str, Any]] = []
    for f in fields:
        if not f.get("required", True):
            continue
        item = dict(f)
        why = WHY_REQUIRED.get(item["key"])
        if why:
            item["why_required_en"] = why["en"]
            item["why_required_ar"] = why["ar"]
        item["critical"] = item["key"] in crit
        item["requirement_banner_en"] = (
            "These questions are required because this business type depends on them."
        )
        item["requirement_banner_ar"] = (
            "هذه الأسئلة مطلوبة لأن نجاح هذا النوع من الأعمال يعتمد عليها."
        )
        out.append(item)
    return out


def missing_required_assumptions(
    archetype: str,
    present_keys: list[str] | set[str] | None,
    *,
    context_text: str | None = None,
) -> list[str]:
    present = {str(k).lower() for k in (present_keys or [])}
    required = required_assumptions_for(archetype, context_text=context_text)
    return [f["key"] for f in required if f["key"].lower() not in present]


def assumption_requirement_explanations(
    archetype: str,
    *,
    language: str = "en",
    context_text: str | None = None,
) -> dict[str, Any]:
    biz = normalize_business_archetype(archetype, context_text=context_text)
    req = required_assumptions_for(biz, context_text=context_text)
    lang = "ar" if language == "ar" else "en"
    special_labels = {
        "fnb": ("F&B / Restaurant / Café", "مطاعم ومقاهي"),
        "marketplace": ("Marketplace / Platform", "سوق / منصة"),
        "healthcare": ("Healthcare", "رعاية صحية"),
        "education": ("Education", "تعليم"),
    }
    if biz in special_labels:
        label = special_labels[biz][0 if lang == "en" else 1]
    else:
        label = ARCHETYPE_LABELS.get(biz if biz in ARCHETYPE_LABELS else "other", {}).get(lang, biz)
    return {
        "archetype": biz,
        "label": label,
        "banner": (
            "These questions are required because this business type depends on them."
            if lang == "en"
            else "هذه الأسئلة مطلوبة لأن نجاح هذا النوع من الأعمال يعتمد عليها."
        ),
        "required_keys": [f["key"] for f in req],
        "critical_keys": sorted(CRITICAL_ASSUMPTION_KEYS.get(biz, frozenset())),
        "fields": req,
    }

"""Lightweight sector intelligence packs (NOT benchmarks / NOT Phase 9A).

Defines what questions, evidence themes, financial inputs, and risks matter.
Does not include market ranges, competitor scores, or industry averages.
"""
from __future__ import annotations

from typing import Any

SECTOR_PACK_IDS = ("fnb", "manufacturing", "saas")

_SECTOR_PACKS: dict[str, dict[str, Any]] = {
    "fnb": {
        "id": "fnb",
        "label_en": "Food & Beverage",
        "label_ar": "أغذية ومشروبات",
        "archetypes": ["fnb"],
        "required_research_areas": [
            "local_demand",
            "competitor_pricing",
            "rent_location_economics",
            "labor_availability",
            "licensing",
        ],
        "critical_assumptions": [
            "seats_capacity",
            "avg_ticket",
            "daily_covers",
            "rent_monthly",
            "food_cost_pct",
            "labor_monthly",
            "operating_hours",
        ],
        "evidence_requirements": [
            "pricing",
            "competitors",
            "location_economics",
            "demand",
        ],
        "financial_inputs": [
            "initial_fitout_capex",
            "monthly_rent",
            "monthly_labor",
            "food_cogs_pct",
            "daily_revenue_capacity",
        ],
        "risk_areas": [
            "location_footfall",
            "food_cost_inflation",
            "labor_retention",
            "licensing_delays",
            "delivery_dependency",
        ],
        "decision_gates": [
            "missing_pricing_evidence_blocks_strong_go",
            "missing_location_economics_requires_conditions",
            "revenue_vs_capacity_validation",
        ],
        "note": "Questions and gates only — no benchmark values.",
    },
    "manufacturing": {
        "id": "manufacturing",
        "label_en": "Manufacturing / Industrial",
        "label_ar": "تصنيع / صناعي",
        "archetypes": ["industrial"],
        "required_research_areas": [
            "feedstock_supply",
            "offtake_demand",
            "capex_equipment",
            "utilities_energy",
            "industrial_regulation",
        ],
        "critical_assumptions": [
            "production_capacity",
            "utilization",
            "capex_machinery",
            "raw_material_cost",
            "selling_price",
            "workforce",
            "energy_cost",
        ],
        "evidence_requirements": [
            "capex",
            "supply_chain",
            "demand",
            "regulation",
        ],
        "financial_inputs": [
            "machinery_capex",
            "facility_capex",
            "variable_cost_per_unit",
            "utilization_pct",
            "unit_selling_price",
        ],
        "risk_areas": [
            "feedstock_volatility",
            "utilization_shortfall",
            "permit_delay",
            "offtake_concentration",
            "energy_tariff",
        ],
        "decision_gates": [
            "capex_validation_required",
            "utilization_validation_required",
            "supply_chain_evidence_required_for_go",
        ],
        "note": "Questions and gates only — no benchmark values.",
    },
    "saas": {
        "id": "saas",
        "label_en": "SaaS / Digital Platform",
        "label_ar": "برمجيات كخدمة / منصة رقمية",
        "archetypes": ["saas_digital"],
        "required_research_areas": [
            "competitor_landscape",
            "pricing_model",
            "acquisition_channels",
            "retention_churn",
            "regulatory_compliance",
        ],
        "critical_assumptions": [
            "target_customers",
            "pricing",
            "arr",
            "cac",
            "churn",
            "acquisition_channels",
        ],
        "evidence_requirements": [
            "pricing",
            "competitors",
            "acquisition",
            "retention",
        ],
        "financial_inputs": [
            "subscription_price",
            "year1_customers",
            "cac",
            "monthly_churn",
            "gross_margin",
        ],
        "risk_areas": [
            "cac_inflation",
            "churn_spike",
            "compliance_cost",
            "sales_cycle_elongation",
            "competition",
        ],
        "decision_gates": [
            "cac_churn_validation",
            "missing_competitor_evidence_blocks_strong_go",
            "financial_consistency_irr_payback",
        ],
        "note": "Questions and gates only — no benchmark values.",
    },
}


def list_sector_packs() -> list[dict[str, Any]]:
    return [dict(_SECTOR_PACKS[i]) for i in SECTOR_PACK_IDS]


def get_sector_pack(pack_id: str) -> dict[str, Any] | None:
    key = (pack_id or "").lower().strip()
    aliases = {
        "fnb": "fnb",
        "food_beverage": "fnb",
        "f&b": "fnb",
        "restaurant": "fnb",
        "manufacturing": "manufacturing",
        "industrial": "manufacturing",
        "factory": "manufacturing",
        "saas": "saas",
        "saas_digital": "saas",
        "software": "saas",
    }
    mapped = aliases.get(key, key)
    pack = _SECTOR_PACKS.get(mapped)
    return dict(pack) if pack else None


def sector_pack_for_archetype(archetype: str) -> dict[str, Any] | None:
    arch = (archetype or "").lower().strip()
    for pack in _SECTOR_PACKS.values():
        if arch in pack["archetypes"] or arch == pack["id"]:
            return dict(pack)
    if arch in {"fnb", "healthcare", "education"}:
        return dict(_SECTOR_PACKS["fnb"])
    if arch in {"industrial", "manufacturing"}:
        return dict(_SECTOR_PACKS["manufacturing"])
    if arch in {"saas_digital", "saas"}:
        return dict(_SECTOR_PACKS["saas"])
    return None

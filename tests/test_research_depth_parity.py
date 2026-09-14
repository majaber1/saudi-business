"""Research depth parity — commercial discovery, location, estimates, synthesis."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

if not os.environ.get("DATABASE_URL"):
    _tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    _tmp.close()
    os.environ["DATABASE_URL"] = "sqlite:///" + _tmp.name

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "backend"))

from ai_engine.hardening.incomplete_evidence_synthesis import (  # noqa: E402
    build_incomplete_evidence_synthesis,
)
from ai_engine.research.market.competitor import research_competitors  # noqa: E402
from ai_engine.research.market.location_economics import (  # noqa: E402
    extract_location_economics,
)
from ai_engine.research.market.operating_estimates import (  # noqa: E402
    apply_estimates_to_assumptions,
    synthesize_operating_estimates,
)
from ai_engine.research.market.planner import classify_research_types  # noqa: E402
from ai_engine.research.planner import build_research_plan, classify_gap  # noqa: E402
from ai_engine.models.study_state import Assumption  # noqa: E402


def test_commercial_discovery_in_gap_classification():
    keys = classify_gap("Local competitors and pricing near Olaya for specialty coffee")
    assert "commercial_discovery" in keys


def test_research_plan_includes_commercial_for_local_venue():
    plan = build_research_plan(
        study_id="t1",
        gaps=["Competitor discovery for cafe in Riyadh"],
        sector="F&B",
        geography="Olaya, Riyadh, Saudi Arabia",
        business_idea="specialty coffee shop",
    )
    keys = [s.source_key for s in plan.sources]
    assert "commercial_discovery" in keys
    assert len(plan.queries) >= 3


def test_location_research_type_forced_for_local_venues():
    types = classify_research_types("specialty coffee shop in Olaya Riyadh", "F&B")
    assert "LOCATION" in types
    assert "COMPETITOR" in types
    assert "PRICING" in types


def test_competitor_extraction_from_osm_style_evidence():
    items = [
        {
            "statement": (
                "Competitor / local venue evidence: Starbucks. "
                "Location: Starbucks, Olaya, Riyadh. "
                "Relevance: Named amenity/cafe listed in OpenStreetMap near Olaya."
            ),
            "source_url": "https://www.openstreetmap.org/node/1",
            "source_key": "commercial_discovery",
            "document_id": "commercial:competitor_poi:abc",
            "competitor_name": "Starbucks",
            "relevance": "OSM cafe near Olaya for local competitor discovery",
        },
        {
            "statement": (
                "Competitor / local venue evidence: Urth Caffe. Location: Urth Caffe, Olaya."
            ),
            "source_url": "https://www.openstreetmap.org/node/2",
            "source_key": "commercial_discovery",
            "document_id": "commercial:competitor_poi:def",
            "competitor_name": "Urth Caffe",
        },
    ]
    comps, status = research_competitors(
        business_idea="specialty coffee",
        sector="F&B",
        geography="Olaya, Riyadh",
        evidence_items=items,
    )
    names = {c.name for c in comps if c.name}
    assert "Starbucks" in names
    assert "Urth Caffe" in names
    assert status == "VERIFIED"
    assert all(c.relevance_reason for c in comps if c.name)


def test_competitor_not_found_requires_exhaustion_doc():
    comps, status = research_competitors(
        business_idea="x",
        sector="y",
        evidence_items=[
            {
                "statement": "Commercial discovery search exhaustion record. NOT_FOUND justification.",
                "source_key": "commercial_discovery",
                "document_id": "ex1",
            }
        ],
    )
    assert status == "NOT_FOUND"
    assert comps[0].search_exhaustion is not None


def test_location_economics_from_density_and_wiki():
    items = [
        {
            "statement": (
                "Location economics — competition density: approximately 14 "
                "OpenStreetMap 'cafe' amenities within 1500m of lat=24.6900, lon=46.6800. "
                "This is a footfall/competition-density proxy for district operating context."
            ),
            "source_url": "https://overpass-api.de/api/interpreter",
            "source_key": "commercial_discovery",
            "document_id": "dens1",
            "evidence_kind": "competition_density",
        },
        {
            "statement": (
                "Location economics / district operating context for Olaya (Riyadh): "
                "Al-Olaya is the central business district of Riyadh."
            ),
            "source_url": "https://en.wikipedia.org/wiki/Olaya_(Riyadh)",
            "source_key": "commercial_discovery",
            "document_id": "wiki1",
            "evidence_kind": "location_context",
        },
    ]
    signals, status = extract_location_economics(
        evidence_items=items, geography="Olaya, Riyadh"
    )
    assert status in {"VERIFIED", "PARTIAL"}
    factors = {s.factor for s in signals}
    assert "competition_density" in factors
    assert any(s.value == 14 for s in signals if s.factor == "competition_density")


def test_operating_estimate_only_from_sourced_numerics():
    items = [
        {
            "statement": "Commercial rent signal Olaya: SAR 18000 per month for retail shop unit.",
            "source_url": "https://en.wikipedia.org/wiki/Riyadh",
            "source_key": "commercial_discovery",
            "document_id": "r1",
            "geography": "Olaya, Riyadh",
        },
        {
            "statement": "Average menu price signal specialty coffee SAR 22 ticket.",
            "source_url": "https://en.wikipedia.org/wiki/Riyadh",
            "source_key": "commercial_discovery",
            "document_id": "p1",
        },
    ]
    estimates = synthesize_operating_estimates(
        evidence_items=items, geography="Olaya, Riyadh"
    )
    by_key = {e.key: e for e in estimates}
    assert "rent_monthly" in by_key
    assert by_key["rent_monthly"].provenance_class == "SYSTEM_ESTIMATE"
    assert by_key["rent_monthly"].source_urls
    assert "avg_ticket" in by_key

    assumptions = [
        Assumption(
            key="rent_monthly",
            value="UNKNOWN",
            source="Unknown",
            confidence="low",
            provenance_class="UNKNOWN",
            origin="default",
        ),
        Assumption(
            key="avg_ticket",
            value="UNKNOWN",
            source="Unknown",
            confidence="low",
            provenance_class="UNKNOWN",
            origin="default",
        ),
        Assumption(
            key="owner_budget",
            value="450000",
            source="user",
            confidence="confirmed",
            provenance_class="USER_PROVIDED",
            origin="user",
        ),
    ]
    filled = apply_estimates_to_assumptions(assumptions, estimates)
    rent = next(a for a in filled if a.key == "rent_monthly")
    assert rent.value != "UNKNOWN"
    assert rent.provenance_class == "SYSTEM_ESTIMATE"
    budget = next(a for a in filled if a.key == "owner_budget")
    assert budget.value == "450000"


def test_no_estimate_without_numbers():
    estimates = synthesize_operating_estimates(
        evidence_items=[
            {
                "statement": "No numbers here, only qualitative district character.",
                "source_url": "https://en.wikipedia.org/wiki/Riyadh",
                "source_key": "commercial_discovery",
            }
        ]
    )
    assert estimates == []


def test_incomplete_evidence_synthesis_actionable():
    assumptions = [
        Assumption(
            key="owner_budget",
            value="450000",
            source="user",
            confidence="confirmed",
            provenance_class="USER_PROVIDED",
            origin="user",
        ),
        Assumption(
            key="rent_monthly",
            value="18000",
            source="SYSTEM_ESTIMATE",
            confidence="medium",
            provenance_class="SYSTEM_ESTIMATE",
            origin="ai_estimated",
            low="15000",
            base="18000",
            high="22000",
        ),
        Assumption(
            key="avg_ticket",
            value="UNKNOWN",
            source="Unknown",
            confidence="low",
            provenance_class="UNKNOWN",
            origin="default",
        ),
        Assumption(
            key="daily_covers",
            value="UNKNOWN",
            source="Unknown",
            confidence="low",
            provenance_class="UNKNOWN",
            origin="default",
        ),
    ]
    market = {
        "competitors": [
            {"name": "Starbucks", "status": "VERIFIED", "source_url": "https://osm.org/1"},
            {"name": "Urth Caffe", "status": "VERIFIED", "source_url": "https://osm.org/2"},
        ],
        "location_economics": [
            {"factor": "competition_density", "status": "VERIFIED", "value": 14}
        ],
        "pricing_signals": [],
    }
    syn = build_incomplete_evidence_synthesis(
        assumptions=assumptions, market_research=market, language="en"
    )
    assert syn["recommendation"]["commercially_actionable"] is True
    assert syn["parity_self_assessment"]["claude_level_coverage"] == "PASS"
    assert syn["parity_self_assessment"]["investment_grade_study"] == "PASS"
    assert "avg_ticket" in syn["material_missing_evidence"]


def test_mcp_boundary_resolves_commercial_discovery():
    from app.integrations.mcp.boundary import connector_for_key

    conn = connector_for_key("commercial_discovery")
    assert conn.connector_id == "live.commercial_discovery"


def test_commercial_connector_infers_amenity_generically():
    from app.integrations.sources.commercial_discovery import infer_amenity_tag

    assert infer_amenity_tag("specialty coffee Olaya") == "cafe"
    assert infer_amenity_tag("dental clinic Riyadh") == "clinic"
    assert infer_amenity_tag("fitness gym Jeddah") == "fitness_centre"


def test_location_city_flows_into_research_geography():
    from ai_engine.research.market.planner import extract_market_context_from_state
    from ai_engine.research.planner import extract_gaps_from_state
    state = {
        "study_id": "t",
        "profile": {"sector": "F&B", "archetype": "fnb", "decision_goal": "feasibility"},
        "structured_answers": {"location_city": "Olaya, Riyadh, Saudi Arabia"},
        "claims": [],
    }
    ctx = extract_market_context_from_state(state)
    assert "Olaya" in ctx["geography"]
    gaps = extract_gaps_from_state(state)
    assert any("Olaya" in g for g in gaps)

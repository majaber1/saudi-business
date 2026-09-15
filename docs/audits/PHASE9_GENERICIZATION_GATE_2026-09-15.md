# Phase 9 Genericization Gate (P3)

**Date**: 2026-09-15
**Gate**: P3 — Bounded Domain Generalization Test
**Purpose**: Verify that the platform structurally supports non-Coffee business archetypes without Coffee/F&B-specific hardcoding blocking the workflow.

---

## Test Method

Deterministic verification of the archetype classification, assumption schema, structured questions, evidence pipeline, financial input structure, and decision gates for two radically different business archetypes against current `main` (`a27e712`).

This is NOT a quality-parity study. This is NOT a research sprint. This is a structural genericization gate.

---

## Scenario A: Scrap / Recycling

**Input (Arabic)**: مصنع إعادة تدوير خردة ومعادن في جدة - شراء خردة حديد ونحاس وألمنيوم وبيع مواد معاد تدويرها

**Input (English)**: Scrap metal recycling plant in Jeddah - buying iron, copper, aluminum scrap and selling recycled materials

### Results

| Check | Result | Detail |
|-------|--------|--------|
| Business understanding | **PASS** | `classify_archetype()` returns `industrial` for both Arabic and English inputs |
| Archetype/domain classification | **PASS** | Classified as "Industrial / Manufacturing" (صناعي / تصنيع) — correct for scrap/recycling |
| Information needs | **PASS** | 10 structured questions generated, all domain-appropriate |
| Assumption schema | **PASS** | Schema keys: `production_capacity`, `raw_material_cost`, `unit_cost`, `selling_price`, `utilization`, `capex_machinery`, `workforce`, `energy_cost_monthly`, `facility_capex`, `supply_chain_model` |
| Research planning | **PASS** | Study engine accepts industrial archetype, phases progress normally |
| Evidence pipeline | **PASS** | `EvidenceItem` model is archetype-agnostic (study-scoped, no F&B-specific fields) |
| Financial input structure | **PASS** | Industrial schema covers: raw material cost, unit cost, selling price, utilization, capacity — appropriate for scrap economics |
| Decision gates | **PASS** | Decision flow (GO/CONDITIONS/DEFER/NO_GO) is archetype-independent |
| Persistence | **PASS** | `StudyStateRow` stores profile as JSON, archetype-agnostic |
| Coffee/F&B leakage | **NONE** | Zero F&B-specific keys (`seats_capacity`, `daily_covers`, `avg_ticket`, `food_cost_pct`, `delivery_dependency`) in industrial schema. Zero SaaS keys (`cac`, `churn`, `arr`, `mrr`) in industrial schema. |

### Scrap-Specific Structural Observations

The `industrial` archetype covers the core scrap/recycling concepts:

| Scrap/Recycling Concept | Schema Coverage |
|------------------------|-----------------|
| Material/scrap supply | `supply_chain_model` (Own collection / Third-party / Mixed) |
| Purchase price / commodity input | `raw_material_cost` (SAR per unit) |
| Selling price | `selling_price` (SAR per unit) |
| Collection/logistics | `supply_chain_model` selection |
| Yard/facility | `facility_capex` (SAR) |
| Machinery/equipment CAPEX | `capex_machinery` (SAR) |
| Throughput/capacity | `production_capacity` (units/year) |
| Utilization | `utilization` (%) |
| Labor | `workforce` (FTEs) |
| Energy/operating costs | `energy_cost_monthly` (SAR) |
| Licensing/regulatory | Handled by research pipeline, not hardcoded in schema |

### Non-Blocking Backlog Items (Scrap)

- `BACKLOG`: Add `commodity_type` selector (ferrous/non-ferrous/mixed) to industrial schema for metals-specific studies
- `BACKLOG`: Add `collection_radius_km` field for logistics modeling
- `BACKLOG`: Scrap-specific regulatory knowledge (MODON, environmental permits)

---

## Scenario B: SaaS

**Input (Arabic)**: منصة SaaS B2B لإدارة الموارد البشرية في السعودية - اشتراك شهري للشركات المتوسطة والكبيرة

**Input (English)**: B2B SaaS platform for HR management in Saudi Arabia - monthly subscription for mid-size and enterprise companies

### Results

| Check | Result | Detail |
|-------|--------|--------|
| Business understanding | **PASS** | `classify_archetype()` returns `saas_digital` for both Arabic and English inputs |
| Archetype/domain classification | **PASS** | Classified as "SaaS / Digital Platform" (برمجيات / منصة رقمية) — correct for B2B SaaS |
| Information needs | **PASS** | 10 structured questions generated, all domain-appropriate |
| Assumption schema | **PASS** | Schema keys: `target_customers`, `pricing`, `arr`, `mrr`, `cac`, `churn`, `ltv`, `capex`, `opex_annual`, `acquisition_channels` |
| Research planning | **PASS** | Study engine accepts saas_digital archetype, phases progress normally |
| Evidence pipeline | **PASS** | `EvidenceItem` model is archetype-agnostic |
| Financial input structure | **PASS** | SaaS schema covers: subscription pricing, customers, MRR/ARR, churn, CAC, LTV — appropriate for SaaS unit economics |
| Decision gates | **PASS** | Decision flow is archetype-independent |
| Persistence | **PASS** | `StudyStateRow` stores profile as JSON, archetype-agnostic |
| Coffee/F&B leakage | **NONE** | Zero physical-location keys (`rent_or_lease`, `seats_capacity`, `daily_covers`, `food_cost_pct`) in SaaS schema. Zero F&B keys in SaaS schema. |

### SaaS-Specific Structural Observations

| SaaS Concept | Schema Coverage |
|-------------|-----------------|
| Subscription pricing | `pricing` (SAR) |
| Customers/users | `target_customers` (count) |
| MRR / ARR | `mrr` (SAR), `arr` (SAR) |
| Churn / retention | `churn` (monthly %) |
| CAC | `cac` (SAR) |
| LTV | `ltv` (SAR) |
| Growth | Implicit in customer/revenue projections |
| Team cost | Part of `opex_annual` |
| Cloud/software cost | Part of `capex` / `opex_annual` |
| Sales/marketing | `acquisition_channels` (multi-select) |
| Runway / working capital | Derived from financial model |

### Leakage Prevention Verification

The codebase includes explicit leakage guards:

- `SAAS_LEAKAGE_KEYS` (frozenset): `cac`, `churn`, `arr`, `mrr`, `ltv`, `saas_pricing`, etc. — these are blocked from appearing in non-SaaS archetypes
- `assert_no_saas_leakage()` function: raises on any SaaS key in non-SaaS schema
- `MOBILITY_SERVICES_KEYS` (frozenset): `take_rate`, `monthly_trips`, `drivers` — blocked from professional services

### Non-Blocking Backlog Items (SaaS)

- `BACKLOG`: Add `team_size` / `engineering_headcount` as explicit fields (currently covered by `opex_annual`)
- `BACKLOG`: Add `cloud_hosting_monthly` as separate field for infrastructure cost modeling
- `BACKLOG`: SaaS-specific benchmark sources for Saudi market (e.g., MCIT data)

---

## Test Suite Verification

| Test File | Tests | Result |
|-----------|-------|--------|
| `test_archetype_assumption_schemas.py` | 23 | ALL PASS |
| `test_archetype_e2e_scenarios.py` | 4 | ALL PASS |
| `test_product_hardening_sprint.py` (archetype) | 1 | PASS |
| `test_v2_study_engine.py` (archetype) | 1 | PASS |
| **Total archetype tests** | **29** | **ALL PASS** |

Key test coverage:
- `test_classify_golden_scenarios`: Verifies classification for all supported archetypes
- `test_no_saas_leakage_in_non_saas_schemas`: Explicitly verifies no SaaS metric leakage
- `test_scenario_reaches_report_without_saas_leakage`: E2E flow for each archetype
- `test_services_default_is_professional_not_mobility`: Services variant guard

---

## Supported Archetypes (Current)

| Archetype | Label (EN) | Label (AR) | Schema Fields |
|-----------|-----------|-----------|---------------|
| `saas_digital` | SaaS / Digital Platform | برمجيات / منصة رقمية | 10 |
| `real_estate` | Real Estate Development | تطوير عقاري | 7 |
| `data_center` | Data Center / Infrastructure | مركز بيانات / بنية تحتية | 10 |
| `industrial` | Industrial / Manufacturing | صناعي / تصنيع | 10 |
| `retail` | Retail / Trading | تجزئة / تجارة | 6 |
| `fnb` | F&B / Restaurant / Café | مطاعم ومقاهي | 11 |
| `services` | Service Business | أعمال خدمية | 10+ (variant-dependent) |
| `other` | Other | أخرى | Generic fallback |

---

## Coffee/F&B Residue Assessment

| Location | Coffee/F&B Content | Classification |
|----------|-------------------|----------------|
| `ai_engine/archetypes/classifier.py` | F&B keyword list for classification | **CORRECT** — needed to route F&B businesses to F&B schema |
| `ai_engine/archetypes/schemas.py` | `FNB_SCHEMA` with seats, covers, avg_ticket, food_cost | **CORRECT** — F&B-specific schema for F&B businesses only |
| `backend/app/services/opportunities.py` | Barn's Cafe, Dr. Cafe franchise opportunities | **DATA** — catalog entries, not architecture leakage |
| `backend/app/services/quick_idea_check.py` | "cafe", "restaurant" in keyword list | **CORRECT** — industry classification routing |
| `backend/app/services/launch.py` | `average_ticket_size` field | **NON-BLOCKING** — post-decision launch tracking, applicable to retail/F&B |
| `backend/app/models.py` | `average_ticket_size` on launch model | **NON-BLOCKING** — same as above |

**No Coffee-specific hardcoding blocks the workflow for non-Coffee archetypes.**

---

## P3 Gate Verdict

### PASS

The Research → Evidence → Financial → Decision pipeline is structurally generic enough to support both Scrap/Recycling (industrial) and B2B SaaS (saas_digital) archetypes without Coffee-specific hardcoding blocking the workflow.

| Criterion | Scrap/Recycling | SaaS |
|-----------|----------------|------|
| Classification | PASS | PASS |
| Information needs | PASS | PASS |
| Financial structure | PASS | PASS |
| Coffee leakage | NONE | NONE |
| Overall | **PASS** | **PASS** |

# ADR: Phase 9 Business Workspace Mapping

**Status**: PROPOSED — requires owner approval before implementation
**Date**: 2026-09-15
**Decision**: How to support the approved "Business Workspace" product concept using the current persistence layer

---

## Context

The approved product baseline defines **Business Workspace** as the first-class entity representing a business opportunity. The current persistence layer uses `Project` as the equivalent entity. The owner has decided:

- `Project` remains the current persistence entity backing the product concept "Business Workspace"
- Do NOT rename the `projects` table or the `Project` ORM class in Phase 9
- The existing `Project → FeasibilityStudy` 1:N relationship already matches the required `Business Workspace → Studies` structure

The open question is: how to support a Business Workspace that has no feasibility study yet (an existing business with no active evaluation), while preserving study-level `BusinessProfile` snapshots.

## Target Conceptual Model

```
Business Workspace (backed by Project)
    │
    ├── Workspace-level Profile (persistent, study-independent)
    │
    ├── FeasibilityStudy A
    │      └── BusinessProfile snapshot A
    │
    ├── FeasibilityStudy B
    │      └── BusinessProfile snapshot B
    │
    └── ...
```

## Decision

**Recommended option: B — Minimal additive fields on Project**

Add a small set of workspace-level fields directly to the `Project` model/table to support the Business Workspace product concept without introducing a new entity.

## Options Evaluated

### Option A: Additive workspace-level profile entity

Create a new `WorkspaceProfile` model with FK to `projects.id`.

- **Schema impact**: New table `workspace_profiles`, new FK relationship on `Project`
- **Pros**: Clean separation, no alteration of existing `Project` columns
- **Cons**: Additional join for common operations, two profile concepts (workspace-level + study-level) may confuse consumers, ORM relationship overhead
- **Backward compatibility**: Full — additive only
- **Rejected because**: Over-engineering for the current need. The workspace profile fields are few and directly related to the Project entity.

### Option B: Minimal additive fields on Project (RECOMMENDED)

Add nullable columns to the `projects` table:

```python
# Proposed additions to Project model
sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
business_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
is_existing_business: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
workspace_status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
```

- **Schema impact**: ALTER TABLE ADD COLUMN on `projects` (nullable columns, no data loss)
- **Pros**: Simplest migration, no new tables, no new joins, all workspace data on one row
- **Cons**: `Project` table grows wider (7 columns), but all are small/nullable
- **Backward compatibility**: Full — all new columns nullable or have defaults
- **Data backfill**: For existing projects, populate `sector` from `industry` (already exists), `city`/`region` from their first study's `BusinessProfile` if present
- **Rollback**: DROP COLUMN (reversible, no data dependency on new columns initially)

### Option C: JSON workspace_profile column on Project

Add a single `workspace_profile: JSON` column to `projects`.

- **Schema impact**: One new column
- **Pros**: Maximally flexible, single migration
- **Cons**: No column-level indexing, no type safety, harder to query/filter
- **Rejected because**: Structured fields are better for the small, well-defined set of workspace profile attributes. JSON is appropriate for dynamic/extensible data, not for core identity fields.

## Consequences

1. Study-level `BusinessProfile` is preserved as-is — it captures evaluation-time snapshot data
2. Workspace-level fields on `Project` serve the "Business Home" screen and the "My Businesses" list
3. When a new study is created under a workspace, the workspace-level fields seed the study's `BusinessProfile` initial values (copy-on-create, not FK)
4. When a study's `BusinessProfile` is updated, the workspace-level fields are NOT automatically synced (snapshot independence)
5. The `industry` column already on `Project` continues to serve as the primary classification; `sector` provides the more specific archetype-level classification

## Evidence Model Note

Per owner decision, the evidence model is NOT changed. `EvidenceItem` remains scoped to `FeasibilityStudy`. The Phase 9 route `/businesses/:bid/evidence` will aggregate evidence from all studies under that workspace (read-only view), preserving:

- Originating study FK
- Source provenance
- Timestamp
- Confidence
- Classification

Cross-study evidence reuse is deferred to post-Phase-9.

## Migration Requirements

- One Alembic migration: `ALTER TABLE projects ADD COLUMN` for each new field
- Data backfill script: populate `sector`, `city`, `region` from existing `BusinessProfile` rows where available
- No destructive changes
- **Requires owner approval before execution**

## References

- `docs/product-baseline/2026-09-15/09_SCREEN_SPECIFICATIONS.md` — S04a (My Businesses), S04b (Business Home)
- `docs/product-baseline/2026-09-15/08_SCREEN_INVENTORY.md` — Screen inventory
- `backend/app/models.py` — Current `Project` and `BusinessProfile` models

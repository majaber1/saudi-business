# Target architecture

Proposed. Nothing in this file is deployed. Stages 2–6 are not complete.

## Principle

Keep the current stack. Do not add a second orchestration runtime. The LangGraph study graph remains the runner. Deterministic policy stays authoritative. The language model explains a result and cannot raise a verdict above the trust ceiling.

## One owner journey

One workspace should carry a study from idea to recommendation:

1. Profile and discovery.
2. Research with source, URL, and retrieval time on every external claim.
3. Evidence the owner can accept or send back.
4. Assumptions with an explicit percent or ratio on every rate.
5. Archetype financials: line items, monthly and annual cash flow, and scenarios that are not only ±20% multipliers.
6. A recommendation the owner Approves, Rejects, or Requests Modification on.
7. A bilingual report, including RTL Arabic, that shows estimate versus owner-confirmed cost and pre-tax operating projection versus investment-ready.

The tabbed study page and `/workspace` converge on that journey. They do not gain a third shell.

## Research

- Keep GASTAT and MISA as live connectors.
- Leave Monsha'at unimplemented until a real, reachable source exists. Do not stub a successful Monsha'at response.
- Allowlisted web search only when a real provider is configured. `not_implemented` stays the result until then.
- A critic step rejects a claim that has no source. It does not invent a citation.
- Competitor rows require identity, URL, and timestamp before they count as evidence.

## Financial model

- Archetype line items replace the single pre-tax operating proxy for investment-ready output.
- Missing material cost stays missing. It never becomes zero and never becomes a sourced fact.
- Estimated fills stay labeled `ESTIMATED` until the owner confirms them.
- Discount rates enter as `PERCENT` or `RATIO`. Stored historical ratios in `[0, 1]` are not rewritten.
- Negative NPV, impossible margins, contradictory evidence, invalid units, and provider failure each block a favorable recommendation.
- Investment-ready output is distinct from the pre-tax operating projection.

## Release boundary

Merge, production migration, and deploy stay behind an explicit owner approval. The recovery branch is the integration line. The dirty `product-readiness/service-architecture` checkout and its colliding `0027` / `0028` revisions are not.

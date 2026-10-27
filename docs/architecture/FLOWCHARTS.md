# Flowcharts

Implemented diagrams describe `recovery/financial-trust-20261028`. Proposed diagrams are not built.

## Implemented study graph

```mermaid
flowchart TD
  startNode[User step] --> discovery[discovery]
  discovery --> research[research]
  research --> evidence[evidence]
  evidence --> assumptions[assumptions]
  assumptions --> financial[financial]
  financial --> risk[risk]
  risk --> decision[decision]
  discovery --> errorHandler[error_handler]
  research --> errorHandler
  evidence --> errorHandler
  assumptions --> errorHandler
  financial --> errorHandler
  risk --> errorHandler
  decision --> errorHandler
  decision --> endNode[END]
```

Each user step runs one phase and then ends. `EVIDENCE_REVIEW` routes back through research before evidence.

## Implemented recommendation ceiling

```mermaid
flowchart TD
  extract[Extract assumptions] --> rate{Discount representation}
  rate -->|absent| defaultRate[Use 0.12 as SYSTEM_DEFAULT_RATIO]
  rate -->|PERCENT or RATIO or percent sign| explicitRate[Use the explicit ratio]
  rate -->|bare number outside 0 to 1| ambiguous[No NPV]
  ambiguous --> insufficient[INSUFFICIENT_EVIDENCE]
  extract --> costs{Operating cost}
  costs -->|missing or all zero with revenue| missingCost[Do not substitute 45 percent]
  missingCost --> insufficient
  costs -->|55 percent or 45 percent fill| estimated[UNVERIFIED_ESTIMATE]
  costs -->|owner supplied| supplied[OWNER_SUPPLIED]
  defaultRate --> compute[NPV IRR payback pre-tax proxy]
  explicitRate --> compute
  estimated --> compute
  supplied --> compute
  compute --> grade{investment_grade}
  grade -->|false estimated cost| ceiling[investment_grade false]
  ceiling --> model[LLM may explain]
  model --> safety[apply_decision_safety]
  safety --> trust[apply_investment_trust]
  trust --> favorable{Verdict would be GO or GO_WITH_CONDITIONS}
  favorable -->|estimated cost| defer[DEFER]
  favorable -->|ambiguous rate| insufficient
  favorable -->|otherwise| keep[Keep the gated verdict]
```

`NO_GO` is not replaced. `INSUFFICIENT_EVIDENCE` replaces `DEFER` when the discount rate is ambiguous.

## Proposed owner journey

```mermaid
flowchart TD
  idea[Business idea] --> researchLive[Live allowlisted research]
  researchLive --> critic[Critic rejects unsourced claims]
  critic --> ownerEvidence[Owner accepts or returns evidence]
  ownerEvidence --> archetype[Archetype line items and cash flow]
  archetype --> scenarios[Scenarios beyond plus or minus 20 percent]
  scenarios --> recommendation[Deterministic recommendation]
  recommendation --> owner{Owner action}
  owner -->|Approve| report[Bilingual report]
  owner -->|Reject| stopNode[Study stopped]
  owner -->|Request modification| idea
```

This journey is proposed. Live Monsha'at and web search are not part of the implemented graph.

# Flowcharts

Implemented diagrams describe `saudi-business-completion`. The financial ceiling shipped on `8f9eac6`. The research ceiling below is the Stage 2 behavior.

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

## Implemented research and competitor contract

```mermaid
flowchart TD
  gaps[Archetype research questions] --> plan[Research plan]
  plan --> live[GASTAT and MISA connectors]
  plan --> blockedMonshaat[Monshaat stays BLOCKED]
  plan --> searchNode[Allowlisted search]
  searchNode --> noKey{Provider credential}
  noKey -->|absent| searchBlocked[BLOCKED and empty results]
  noKey -->|present but client disabled| searchBlocked
  live --> claims[Claims with provenance]
  claims --> cite[Citation critic]
  cite --> lineage[Research critic]
  lineage --> competitors[Competitor verification]
  competitors --> verified{Name and http URL and real timestamp}
  verified -->|yes and geography matches| record[Verified competitor record]
  verified -->|no| mention[Unverified mention]
  lineage --> failed{Research status failed or no source-backed claim}
  failed -->|yes| insufficient[INSUFFICIENT_EVIDENCE]
  failed -->|no| financialGate[Stage 1 financial ceiling]
```

A verified competitor record stores publisher, identity, stated location, retrieval time, and the supporting claim separately. Missing URL and timestamp fields are left empty.

## Implemented evidence provenance

```mermaid
flowchart TD
  source[Source payload] --> kind{Claim kind}
  kind -->|official or document| url{http source URL}
  kind -->|ai assumption| estimate[Kept as an estimate]
  kind -->|owner input| owner[Kept as an owner assumption]
  url -->|missing| reject[Rejected with a reason]
  url -->|present| geo{Country city currency}
  geo -->|conflict| reject
  geo -->|consistent| keep[Source-backed evidence]
  reject --> noFill[No replacement citation is written]
  keep --> persist[Research result carries plan gaps and attempts]
  estimate --> persist
```

Provider errors append to the research error list and keep the run out of `complete`.

## Implemented coffee and SaaS projection

```mermaid
flowchart TD
  archetype{Archetype} -->|fnb| coffee[Revenue rent payroll operating cost]
  archetype -->|saas_digital| saas[Subscription acquisition hosting]
  archetype -->|other| legacy[Existing pre-tax proxy]
  coffee --> lines[Explicit lines with assumption lineage]
  saas --> lines
  lines --> missing{Any material line missing or ambiguous}
  missing -->|yes| insufficient[INSUFFICIENT_EVIDENCE and no zero fill]
  missing -->|no| estimated{Any material line estimated}
  estimated -->|yes| defer[DEFER and NPV withheld]
  estimated -->|no| sign{Monthly net}
  sign -->|negative| nogo[NO_GO]
  sign -->|non-negative| annual[Annual sum of monthly pre-tax flows]
  annual --> scenario[Named driver scenario]
  scenario --> bare{Bare multiplier}
  bare -->|yes| rejected[Scenario rejected]
  bare -->|no| same[Same inputs same cash flows]
```

The cash-flow basis is `PRE_TAX_OPERATING_PROJECTION`. VAT and Zakat are not in the series. The study workspace renders these lines, their lineage, and a stale banner after an assumption edit. A favorable verdict does not survive that edit.

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

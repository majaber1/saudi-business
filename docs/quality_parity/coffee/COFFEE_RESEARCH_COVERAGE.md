# Coffee Research Coverage

Maps decision questions an investment-grade specialty-coffee study should answer, and whether Saudi Business can cover the *class* of question (not Claude’s numbers).

| Decision question | Required research / model | Pre-sprint | Post-sprint |
|---|---|---|---|
| Is SAR 450k sufficient? | CAPEX + WC + budget gap | FAIL (CAPEX=10k) | PASS (budget SURPLUS/SHORTFALL) |
| Plausible café configuration? | seats, hours, area, days | FAIL (10000 placeholders) | PASS/PARTIAL (UNKNOWN or validated) |
| What could rent cost? | location economics | WEAK | PARTIAL (ask / range / flag) |
| Staffing required? | roles + labor cost | WEAK | PARTIAL (labor wired; role depth limited) |
| Revenue drivers? | covers × ticket × days | FAIL (rev=0) | PASS when inputs numeric |
| Cost structure? | COGS + OPEX | FAIL | PASS when inputs numeric |
| CAPEX required? | component CAPEX | FAIL | PASS |
| Working capital? | explicit WC | FAIL | PASS |
| Key competitors? | competitor research | FAIL (empty) | PARTIAL (research forced; evidence-dependent) |
| Pricing environment? | pricing evidence | WEAK | PARTIAL |
| Break-even / CF / NPV / IRR / payback? | wired model | FAIL | PASS when math valid |
| Kill risks? | risk model | PARTIAL | PARTIAL+ |
| Still missing? | gaps / UNKNOWN | PARTIAL | IMPROVED |
| Next owner decision? | decision + questions | SAFETY OK | SAFETY PRESERVED |

## Coverage verdict (implementation stage)

- Operating / financial wiring class: **PASS** (unit/integration tests)
- Research depth / competitors / location: **PARTIAL** until REAL_USER_FLOW evidence confirms live retrieval quality
- Claude-level decision usefulness: pending REAL_USER_FLOW

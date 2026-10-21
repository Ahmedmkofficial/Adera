# Adera MVP risk scoring

## Public API compatibility

`backend.services.risk_engine.calculate_risk(...)` remains the public entry
point. Its original four positional arguments and existing keyword arguments
remain supported. `independent_report_count` overrides legacy `report_count`
when provided. The refactored rules validate inputs, cap the score at 100, and
retain stable human-readable explanations.

## Current scoring retained in Stage 1

No risk weights, thresholds, levels, or recommendations are changed in this
integration stage. The current `develop` scoring remains authoritative:

| Signal                   | Existing points | Conditions                                      |
|:-------------------------|:---------------:|:------------------------------------------------|
| Independent fraud reports| 5 / 10 / 20     | At least 1 / 3 / 7                              |
| Recent reports           | 5 / 15          | At least 1 / 3                                  |
| Previous scam cases      | 15 / 25         | At least 1 / 2                                  |
| Suspicious relationships | 10 / 15         | At least 1 / 2                                  |
| Repeated scam pattern    | 10              | Boolean signal is true                          |
| Unusual transaction      | 10              | Explicit signal is true or amount is at least 5000 |

Risk levels remain:

- 0–24: LOW
- 25–49: MODERATE
- 50–74: HIGH
- 75–100: CRITICAL

Although the implementation caps scores at 100, the current maximum sum of
signal weights is 95. Recommendations remain ALLOW, REVIEW, VERIFY, and
STOP_AND_VERIFY, respectively.

## Feature branch differences deferred

`origin/feature/risk-engine` proposes a new mapping-based input API and
different weights and conditions. For example, two independent reports trigger
its 20-point rule, and unusual transactions are weighted 15. Those differences
are not adopted here because they would silently alter existing risk outcomes
without a product decision. Future scoring changes should update this document
and include approved threshold and weight examples with tests before changing
the implementation.

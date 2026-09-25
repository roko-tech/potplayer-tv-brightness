# Service-level objectives

- Status: Define before production
- Owner: Define
- Review cadence: Define

Choose a small number of indicators tied to important user journeys. Avoid promising host uptime when users care about successful, correct, timely outcomes.

| Journey | SLI definition | Objective/window | Measurement source | Error-budget response | Owner |
| --- | --- | --- | --- | --- | --- |
| Primary journey | Successful valid outcomes / eligible attempts | Define | Define | Define | Define |
| Latency | Proportion under user-relevant threshold | Define | Define | Define | Define |
| Data freshness/correctness | Define | Define | Define | Define | Define |

## Measurement rules

- Define eligible events, exclusions, aggregation, time zones, and missing telemetry behavior.
- Measure from the user-visible boundary where practical.
- Separate dependency failures only if the user experience genuinely excludes them.
- Alert on actionable burn rate or imminent user harm, not every noisy metric movement.
- Use the error budget to guide release pace and reliability work; do not silently redefine the SLI after a miss.

Record planned maintenance, support expectations, and any external SLA separately. Validate that dashboards and alerts calculate the written definition.

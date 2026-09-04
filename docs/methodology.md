# Methodology

## Baseline Calculation
The baseline evaluates historical resource utilization, traffic volume, and latency by calculating key percentiles:
- **P95 and Peak**: To capture bursty or intensive periods that averages miss.
- **Mean**: To provide a generalized view of the workload.

## Workload Projection
When shifting to a candidate instance type, the simulator computes the ratio of CPU and memory capacities between the current and candidate instances. This ratio is applied to historical telemetry to project the theoretical resource utilization on the smaller instance.

## Performance Modeling
- **Latency Penalty**: We apply a non-linear penalty to latency when projected CPU exceeds 75% or memory exceeds 80%. This models the queuing and processing delays typical of saturated systems.
- **Availability Risk**: When projected resources exceed 95%, availability drops proportionally to the magnitude of the violation, reflecting an increased risk of dropped requests and Out-Of-Memory (OOM) kills.

## Cost Estimation
Cost reductions are calculated directly from historical pricing data, producing a percentage-based reduction over a 30-day simulated period.

## Decision Engine Thresholds
The engine enforces strict safety gates:
- A decision is **SAFE TO RIGHTSIZE** only if cost decreases, latency and availability SLOs are met, and peak resource utilization stays within configured safe limits (default 90%).
- Any violation triggers a **DO NOT RIGHTSIZE** decision.


## Agentic Automation
The 9/10 Agentic Maturity upgrade transitions the system from a deterministic user-driven calculator into an autonomous state-machine based actor:
1. **Delegation**: The agent observes the current environment telemetry independently.
2. **Analysis and Planning**: The agent analyzes baseline performance and autonomously selects a candidate migration target.
3. **Validation**: The agent delegates safety checks to the core deterministic DecisionEngine. The safety engine cannot be overridden.
4. **Execution and Verification**: Once migrated in the local mock environment, the agent actively verifies post-migration health.
5. **Adaptive Re-planning**: If a deterministic failure injection causes a post-migration health check to fail, the agent triggers a fully autonomous rollback.

# Deployment Checklist

## CURRENT LOCAL PROTOTYPE (Review 1 ~50-55% Completion)
- [x] Validate telemetry data quality (No missing values, valid ranges).
- [x] Validate pricing data and ensure candidate instance prices are available.
- [x] Configure latency SLO target (e.g., 250ms).
- [x] Configure availability SLO target (e.g., 99.9%).
- [x] Verify baseline metrics match observed production behavior.
- [x] Run simulation for the candidate instance.
- [x] Review sensitivity analysis under varying traffic growth assumptions.
- [x] Validate pre-migration safety checks.
- [x] Execute migration lifecycle against Local Mock Infrastructure.
- [x] Validate automatic rollback triggered via deterministic simulated failures.
- [x] Verify Audit Logging records events accurately.

## FUTURE PRODUCTION DEPLOYMENT
- [ ] Implement live infrastructure API integration (AWS/GCP/Azure) replacing Mock Infrastructure.
- [ ] Connect Data Loader to live telemetry API endpoints.
- [ ] Wire orchestrator pre-check and post-check loops to live observability webhooks.
- [ ] Production-grade rollback strategy implementation (handling DB disconnects, state loss etc).
- [ ] Obtain stakeholder approval for live IaC execution layer integration.


### Agentic Capabilities (Local Only)
- [x] Agent state machine is correctly navigating states (OBSERVING, PLANNING, SIMULATING, VALIDATING).
- [x] Agent is hard-blocked from overriding the Safety Engine (DecisionEngine).
- [x] Failed health checks correctly trigger the execution of the fallback execute_rollback tool.
- [x] All agent transitions are being logged to data/agent_audit_log.csv.

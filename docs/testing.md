# Unit Testing Documentation

## Test Architecture
The test suite is built using `pytest`. The system leverages robust mocks (via `unittest.mock`) to prevent tests from modifying actual external infrastructure or making network calls.

### Test Organization
Tests are logically separated by module domain into the `tests/` directory:
- `test_baseline.py`, `test_simulator.py`: Core simulation logic.
- `test_orchestrator.py`, `test_migration_lifecycle.py`: End-to-end migration execution.
- `test_agent.py`: Agentic workflow and state transitions.
- `test_analysis.py`, `test_sensitivity_error.py`: Sensitivity analysis, error bounds, portfolio savings.

| Test Area | Test File | Purpose | Important Cases |
|-----------|-----------|---------|-----------------|
| Baseline | `test_baseline.py` | Verify metric aggregation | P95 calculations, empty environments |
| Validation | `test_validation.py` | Data integrity pre-checks | Missing data, invalid metrics, edge cases |
| Workload | `test_workload_model.py` | Workload transformations | CPU/Memory pressure, seasonal growth |
| Simulation | `test_simulator.py` | Performance projection | Spikes, non-cheaper candidates, SLO violations |
| Decision Engine | `test_decision_engine.py` | Safety boundary adherence | Safe vs Unsafe migrations |
| Migration | `test_migration_lifecycle.py` | Execution and health monitoring | Successful migration, post-migration degradation |
| Rollback | `test_orchestrator.py` | State restoration | Rollback execution, blocked execution |
| Agent | `test_agent.py` | Autonomous execution | Re-plan triggers, blocking triggers |
| Analysis & Portfolio | `test_analysis.py` | Financial projections and views | Total savings, blocked savings, Stakeholder view generation |
| Sensitivity | `test_sensitivity_error.py` | Edge bounds | CPU pressure failures, Memory pressure failures |
| Security | `test_security.py` | Vulnerability checks | Secrets detection, subprocess/arbitrary execution detection |

## Important Failure Boundaries
The test suite meticulously validates **Safety Boundaries**. For example, in `test_sensitivity_error.py`, when a candidate is projected to reach >100% CPU utilization under traffic growth, the suite explicitly asserts that the system outputs `DO NOT RIGHTSIZE`. No unsafe candidates are permitted to bypass these bounds.

# Performance-Safe Rightsizing Simulator

## Project
- **Title**: Performance-Safe Rightsizing Simulator
- **Problem**: Rightsizing infrastructure decisions based solely on average utilization often result in CPU/Memory saturation, degraded latency, or availability breaches.
- **Objective**: Provide a data-driven, workload-aware decision engine that simulates performance impacts *before* migrations, rejecting unsafe rightsizing attempts.
- **Domain**: Cloud FinOps, Site Reliability Engineering (SRE), and Infrastructure Management.

## Architecture
- **Major Components**: Telemetry ingestion, Baseline/Workload/Performance/Availability modeling engines, Safety Decision Engine, Agentic workflow orchestrator, Post-Migration monitor, Streamlit UI.
- **Data Flow**: `Telemetry -> Simulation -> Safety Engine -> Decision -> Migration/Rejection -> Monitoring -> Audit/Rollback`.
- **Agentic Workflow**: Fully implements an autonomous observation loop (`OBSERVE -> ANALYZE -> PLAN -> VALIDATING -> EXECUTING -> VERIFYING -> RE-PLAN`).

## Core Functionality
- **Telemetry Validation**: Drops invalid/missing/negative metrics before processing.
- **Workload Modeling**: Synthesizes and tests against normal, seasonal, and peak traffic pressure conditions.
- **Candidate Selection**: Intelligently ranks and selects cheaper instance types.
- **Simulation**: Accurately projects target P95 latency and memory impacts based on CPU correlations.
- **Safety Engine**: Explicitly rejects candidates violating defined P95 Latency or Availability constraints.
- **Migration**: Automates state transition in local mock infrastructure.
- **Monitoring**: Observes checkpoint health immediately post-migration.
- **Rollback**: Dynamically restores the original instance if degradation is observed.
- **Portfolio Analysis**: Scans all 73 environments, differentiating safe vs. blocked aggregate savings.
- **Sensitivity Analysis**: Validates boundary adherence across variables like `traffic_growth` and `cpu_pressure`.
- **Explainability**: Generates precise JSON justifications mapping exact metrics to safety rejection reasons.

## Testing
- **Exact Current Test Count**: 72
- **How to Run Tests**: Execute `python -m pytest -q` in the terminal.
- **Test Categories**: Validation, Simulation, Lifecycle, Agentic, Sensitivity, Security, Portfolio Analysis.
- **Important Failure Scenarios**: Simulates post-migration SLA violation, triggering successful orchestrator rollback. Explicitly tests >100% CPU projection failure bounds.

## Error Handling
- **Validation Failures**: Blocks environment evaluation.
- **Blocked Rightsizing**: Enforces "DO NOT RIGHTSIZE" and aborts the migration workflow if bounds are broken.
- **Migration Failures**: Simulated local mock injection handled robustly via localized error responses.
- **Rollback**: Handled securely via the Orchestrator with critical escalations if simulated state restoration fails.
- *Detailed behavior mapping is located in `docs/error_handling.md`*.

## API
- **Application Architecture**: This project is built as a **local Python application and Streamlit dashboard**. 
- **Actual Endpoints**: **None.** No FastAPI/Flask/REST API endpoints exist. All operations are accessible via Python library modules or the Streamlit UI.
- *Details in `docs/api.md`*.

## Data & Database
- **Actual Storage Mechanism**: Flat files (CSV) and in-memory DataFrames (Pandas). The system does not use a persistent relational database like PostgreSQL.
- **Actual Schema**: No active database schemas exist. Infrastructure is modeled locally via `src/mock_infrastructure.py`.
- *Details in `docs/database_schema.md`*.

## Security
- **Input Validation**: Hard validations on data types and bounds within telemetry parsers.
- **Command Execution Controls**: Explicitly validated via unit tests to ensure `os.system` and `subprocess` are not used maliciously in source logic.
- **Secret Handling**: Zero API keys or secrets are committed. Test-enforced via automated keyword scanning.
- **Audit Logging**: Robust append-only ledger in CSV format ensuring non-repudiation of agentic decisions.

## Local Setup
1. **Installation**: `pip install -r requirements.txt`
2. **Dataset Generation**: `python scripts/generate_dataset.py`
3. **Demos**: 
   - `python scripts/run_experiment.py`
   - `python scripts/run_migration_demo.py`
   - `python scripts/run_agent_demo.py`
   - `python scripts/final_demo.py`
4. **Dashboard Startup**: `streamlit run app/dashboard.py`

## Limitations
- **Local Mock Infrastructure**: Operations do not interact with actual AWS/GCP APIs; all state transitions are simulated in a local dictionary structure.
- **Simulated Observations**: Post-migration metrics are simulated based on deterministic rules, not pulled from live Datadog/Prometheus endpoints.
- **Simulated Stakeholder Validation**: Persona views (FinOps, Infrastructure, Service Owner) are static logic responses, not actual human interaction layers.
- **Potential vs Realized Savings**: Cost metrics represent potential theoretical savings; actual billing data may vary.

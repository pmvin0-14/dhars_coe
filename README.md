# Performance-Safe Rightsizing Simulator

## Problem Statement
The organization currently performs cost-saving actions such as rightsizing infrastructure instances. However, rightsizing decisions are often based on incomplete or averaged usage information. A cheaper instance can sometimes cause CPU saturation, memory pressure, increased latency, request-processing degradation, and availability/SLO violations.

## Objective
Build a working workload-aware rightsizing simulator that compares the cost and service-level impact of moving an environment from its current instance type to a cheaper candidate instance type. 

## Key Features
- **Workload-Aware Simulation**: Projects resource utilization (CPU, memory), latency, and availability risks based on realistic historical workloads.
- **Service-Level Validation**: Rejects rightsizing if strict latency or availability SLOs are violated.
- **Interactive UI**: A Streamlit dashboard to explore scenarios, run simulations, and visualize performance vs. cost trade-offs.
- **Sensitivity Analysis**: Evaluates decisions against future traffic growth.

## Architecture
See `docs/architecture.md` for a detailed architecture diagram.
- **Data**: Synthetic historical telemetry.
- **Engine**: Baseline calculation, Workload Model, Performance Model, Cost Model, Availability Model, Decision Engine.
- **UI**: Streamlit application.
- **Execution**: Local Mock Infrastructure module that models in-memory instances.
- **Audit**: Durable CSV ledger logging every state change.

## How to Run

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate Synthetic Data**
   ```bash
   python scripts/generate_dataset.py
   ```

3. **Run Experiments (3 Scenarios)**
   ```bash
   python scripts/run_experiment.py
   ```

4. **Run Local Mock Migration Demo**
   ```bash
   python scripts/run_migration_demo.py
   ```

5. **Launch Dashboard**
   ```bash
   streamlit run app/dashboard.py
   ```

6. **Run Tests**
   ```bash
   pytest -q
   ```

## Status
The current prototype represents approximately **50–55% of the overall project scope**. 
The core data pipeline, baseline analysis, rightsizing simulation, operating scenarios, safety decision engine, automated testing, dashboard, initial sensitivity analysis, and an executable **LOCAL MOCK INFRASTRUCTURE** state machine with audit logging and rollback capabilities are implemented. This demonstrates the safety gate effectively without requiring external dependencies or real cloud deployments.

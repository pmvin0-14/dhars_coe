# Localhost Demonstration Walkthrough

This walkthrough outlines how to execute the end-to-end Local Mock Infrastructure migration lifecycle.

## 1. Environment Preparation
First, generate the synthetic dataset required to drive the simulator.
```bash
python scripts/generate_dataset.py
```

## 2. Programmatic Lifecycle Demonstration
Run the newly created migration demo script to see the state machine in action.
```bash
python scripts/run_migration_demo.py
```
Observe the terminal output as it iterates through:
- **FLOW A**: Safe Migration
- **FLOW B**: Blocked Migration (demonstrating the Safety Gate)
- **FLOW C**: Rollback (demonstrating deterministic failure injection)

## 3. UI Dashboard Demonstration
Launch the interactive UI:
```bash
streamlit run app/dashboard.py
```
Open `http://localhost:8501`.

1. **Select an environment** from the left sidebar (e.g. `env-007` for Normal/Safe, `env-003` for Bursty).
2. **Review the Baseline and Simulation Results**.
3. Scroll down to the **Migration Lifecycle (LOCAL MOCK INFRASTRUCTURE)** section.
4. Click **Execute Migration Lifecycle**.
5. Observe the execution log transitioning through PRECHECK, MIGRATION, and POSTCHECK phases.
6. Verify the Audit Log updates.
7. To test rollback, check the "SIMULATED FAILURE INJECTION" box and click execute again. Watch the system catch the failure and perform a simulated rollback to restore the original instance.


## Agentic Capabilities (Local Execution)

The system now features an autonomous rightsizing agent that executes the safety logic programmatically.

1. **Start the Agent Demo:**
   \\ash
   python scripts/run_agent_demo.py
   \   
2. **Observe Scenarios:**
   - **Scenario 1:** Demonstrates the end-to-end autonomous lifecycle in a safe environment.
   - **Scenario 2:** Demonstrates the agent correctly blocking an unsafe migration.
   - **Scenario 3:** Simulates a post-migration health check failure and demonstrates the agent autonomously triggering a rollback to restore the environment state.
   - **Scenario 4:** Performs a Portfolio Analysis across all 73 viable environments, proving that 100% of unsafe migrations (3 out of 34 evaluated) were blocked by the safety engine.

3. **Check the Audit Log:**
   All agent transitions and actions are durably written to \data/agent_audit_log.csv\.


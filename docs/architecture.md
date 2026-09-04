# Architecture

## Rightsizing Simulator Architecture

```mermaid
graph TD
    A[Historical Telemetry Data] --> B[Data Validator]
    B --> C[Baseline Engine]
    C --> D[Workload Model]
    D --> E[Performance Model]
    E --> F[Availability Model]
    A --> G[Cost Model]
    F --> H[Decision Engine]
    G --> H
    H --> I[Streamlit Dashboard]
    
    J[Legacy Workflow: Manual Rightsizing] --> K[Rightsizing Simulator Safety Gate]
    K -- SAFE --> L[Local Mock Infrastructure Migration]
    K -- BLOCK --> M[Migration Prevented]
    
    L --> N[Post-Migration Check]
    N -- SLO Violated --> O[ROLLBACK Triggered]
```

### Agentic Intelligence Layer

The system has been upgraded to a 9/10 Agentic Maturity level by introducing an autonomous `RightsizingAgent`. This agent controls the end-to-end rightsizing lifecycle without bypassing any safety thresholds. 

The agent operates as a finite state machine:
`OBSERVING -> ANALYZING -> PLANNING -> VALIDATING -> EXECUTING -> VERIFYING -> COMPLETED / ROLLED_BACK / BLOCKED`

```mermaid
graph TD
    OBS[OBSERVING] --> ANA[ANALYZING]
    ANA --> PLN[PLANNING]
    PLN --> VAL[VALIDATING]
    
    VAL -- SAFE --> EXE[EXECUTING]
    VAL -- DO NOT RIGHTSIZE --> BLK[BLOCKED]
    
    EXE --> VER[VERIFYING]
    VER -- HEALTHY --> CMP[COMPLETED]
    VER -- DEGRADED --> RPL[RE_PLAN]
    
    RPL --> RBK[ROLLED_BACK]
```

### Components

1. **Agent Tools (`AgentTools`)**: Exposes programmatic functions (e.g. `load_telemetry`, `simulate_rightsizing`, `execute_local_migration`, `run_health_check`) to the agent, shielding the underlying deterministic implementation.
2. **Rightsizing Agent (`RightsizingAgent`)**: Navigates the state machine autonomously. It handles risk scoring, trace logging, and programmatic rollback handling upon encountering failure.
3. **Safety Engine (`DecisionEngine`)**: Remained immutable. The agent cannot override or bypass it.
4. **Mock Infrastructure (`LocalInfrastructure`)**: Holds an in-memory representation of instance types.
5. **Audit Ledger (`AuditLog`)**: Records every autonomous decision made by the agent for compliance and observability.

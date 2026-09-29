# Error Handling & Boundaries

## Architecture
Error handling is localized within `src/error_handler.py`, ensuring consistent responses across the pipeline. 

The flow follows:
`INPUT` → `VALIDATION` → `PROCESSING` → `FAILURE DETECTION` → `ERROR RESPONSE` → `RECOVERY / SAFE EXIT`

## Key Failure Cases

### 1. Telemetry Data Missing/Invalid
- **Trigger**: Ingestion layer receives incomplete or corrupt CSV rows.
- **Detection**: `DataValidator.validate_telemetry()` triggers.
- **System Response**: Flags error code `INVALID_TELEMETRY`.
- **Recovery Behavior**: Aborts rightsizing evaluation for the affected environment. Migration is prevented.

### 2. Candidate SLO Violation (Safety Engine)
- **Trigger**: The projected P95 latency or availability exceeds strict thresholds (e.g., >250ms).
- **Detection**: `DecisionEngine.evaluate()` projects constraint violations.
- **System Response**: Returns `DO NOT RIGHTSIZE`.
- **Recovery Behavior**: Graceful fallback to `monitor current instance`. Migration is explicitly prevented.

### 3. CPU/Memory Saturation
- **Trigger**: Advanced sensitivity analysis applies traffic growth, leading to >100% resource utilization.
- **Detection**: `Simulator` calculates peak values > 100%.
- **System Response**: Flags `CPU_SATURATION` or `MEMORY_SATURATION`.
- **Recovery Behavior**: Aborts rightsizing. Migration is prevented.

### 4. Post-Migration Health Degradation
- **Trigger**: Immediate checkpoints following a mock infrastructure migration reveal >1% error rates or latency violations.
- **Detection**: `PostMigrationMonitor.evaluate_health()` returns `DEGRADED`.
- **System Response**: The `MigrationOrchestrator` intercepts the degraded state.
- **Recovery Behavior**: Triggers automatic rollback to the previous infrastructure state via `orchestrator.trigger_rollback()`.

### 5. Rollback Failure
- **Trigger**: The mock infrastructure fails to restore the prior state.
- **Detection**: Caught within `trigger_rollback()`.
- **System Response**: Flags `ROLLBACK_FAILURE`.
- **Recovery Behavior**: Escalate to SRE (Critical failure). Manual intervention required.

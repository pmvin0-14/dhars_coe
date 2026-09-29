# Database Schema Documentation

## Overview

The Performance-Safe Rightsizing Simulator **does not use a persistent relational database** (like PostgreSQL or MySQL). 

Instead, the system relies on:
1. **Local CSV files (`data/` directory):** Used to load synthetic telemetry, environments, and pricing history.
2. **In-Memory DataFrames (Pandas):** All processing and simulation are performed in memory.
3. **Local Mock Infrastructure (`src/mock_infrastructure.py`):** An in-memory dictionary-based registry simulating infrastructure states and active instance types.
4. **Audit Log File (`data/dashboard_audit_log.csv`):** A CSV-backed append-only log capturing all migration events, rollbacks, and safety decisions.

No SQL database schema is fabricated or utilized by this system.

# API Documentation

## Overview

The Performance-Safe Rightsizing Simulator is a **local Python application and Streamlit dashboard**. 
It **does not expose any web API endpoints** (such as REST, FastAPI, or Flask).

All interaction occurs via:
1. **Command Line Interface (CLI):** Scripts in the `scripts/` directory.
2. **Streamlit Web Dashboard:** Running locally on port 8501 via `streamlit run app/dashboard.py`.
3. **Python Module Imports:** Internal modules like `src.orchestrator.MigrationOrchestrator` are used as Python libraries.

No HTTP APIs are fabricated or exposed by this system.

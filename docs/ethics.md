# Ethics Note

- **Cost optimization must not override reliability**: Safety gates prevent rightsizing if latency or availability targets are projected to be violated.
- **Uncertainty must be communicated**: The simulator projects estimates based on a simplified model and assumptions (like traffic growth). It is not an exact guarantee.
- **No automatic high-risk migration without approval**: The simulator operates as an advisor and a safety gate, but human oversight should remain for production changes.
- **Telemetry should be handled responsibly**: Only required metrics are processed.
- **Synthetic data**: The data used in this prototype is synthetic and clearly labeled as such. Simulated predictions must not be presented as real measurements.
- **Rollback must remain available**: Despite predictive modeling, unexpected issues can occur. Automated rollback mechanisms are critical for safety.


## Agentic Autonomy and Safety
The rightsizing agent has full autonomy over state transitions, but **zero autonomy over safety thresholds**.
- The RightsizingAgent is structurally forbidden from modifying the risk tolerance parameters of the DecisionEngine.
- The agent is designed to prioritize conservative ROLLBACK states over remaining in degraded states.
- The agent does not interact with any external production infrastructure, reducing the risk of blast radius damage during exploration.

class ErrorHandler:
    @staticmethod
    def handle_error(error_code, env_id, details=None):
        """
        Explicitly handles all failure/edge cases.
        """
        errors = {
            "MISSING_TELEMETRY": "Telemetry data is missing.",
            "INVALID_TELEMETRY": "Telemetry data is invalid or corrupt.",
            "DUPLICATE_TELEMETRY": "Telemetry data contains duplicate timestamps.",
            "UNKNOWN_ENVIRONMENT": "Environment ID not found in registry.",
            "NEGATIVE_REQUEST_VOLUME": "Request volume contains negative values.",
            "NEGATIVE_LATENCY": "Latency contains negative values.",
            "CPU_SATURATION": "CPU utilization exceeds 100%.",
            "MEMORY_SATURATION": "Memory utilization exceeds 100%.",
            "LATENCY_SLO_FAILURE": "Latency exceeds SLO target.",
            "AVAILABILITY_SLO_FAILURE": "Availability falls below SLO target.",
            "INSUFFICIENT_TELEMETRY": "Not enough telemetry data points (e.g., < 24h).",
            "NO_COST_BENEFIT": "Candidate instance does not provide cost savings.",
            "SAME_CANDIDATE": "Candidate instance is identical to current instance.",
            "NO_SAFE_CANDIDATE": "No candidate passed safety evaluation.",
            "MIGRATION_FAILURE": "Infrastructure migration execution failed.",
            "POST_MIGRATION_HEALTH_FAILURE": "Post-migration checkpoints deemed unhealthy.",
            "ROLLBACK_FAILURE": "Failed to restore original infrastructure state.",
            "INVALID_AGENT_STATE": "Agent reached an unknown or invalid state."
        }
        
        reason = errors.get(error_code, "Unknown error occurred.")
        
        recovery_action = "Manual intervention required."
        if error_code in ["MISSING_TELEMETRY", "INVALID_TELEMETRY", "INSUFFICIENT_TELEMETRY", "NEGATIVE_REQUEST_VOLUME", "NEGATIVE_LATENCY", "DUPLICATE_TELEMETRY"]:
            recovery_action = "Check telemetry pipeline and re-ingest data."
        elif error_code in ["NO_COST_BENEFIT", "SAME_CANDIDATE", "NO_SAFE_CANDIDATE", "LATENCY_SLO_FAILURE", "AVAILABILITY_SLO_FAILURE", "CPU_SATURATION", "MEMORY_SATURATION"]:
            recovery_action = "Abort rightsizing. Monitor current instance."
        elif error_code == "POST_MIGRATION_HEALTH_FAILURE":
            recovery_action = "Trigger automatic rollback."
        elif error_code == "MIGRATION_FAILURE":
            recovery_action = "Retry migration or abort."
        elif error_code == "ROLLBACK_FAILURE":
            recovery_action = "CRITICAL: Escalate to SRE. Manual rollback required."
            
        return {
            "status": "FAILED",
            "error_code": error_code,
            "reason": reason,
            "environment": env_id,
            "details": details,
            "recovery_action": recovery_action
        }

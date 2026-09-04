from src.data_loader import DataLoader
from src.simulator import Simulator
from src.decision_engine import DecisionEngine
from src.mock_infrastructure import LocalInfrastructure
from src.audit_log import AuditLog

class AgentTools:
    def __init__(self, simulator: Simulator, infrastructure: LocalInfrastructure, audit_log: AuditLog, data_loader: DataLoader = None):
        self.simulator = simulator
        self.infrastructure = infrastructure
        self.audit_log = audit_log
        self.data_loader = data_loader or DataLoader('data')

    def load_telemetry(self, env_id):
        envs_df = self.data_loader.load_environments()
        if env_id not in envs_df['environment_id'].values:
            return None, "Environment not found"
        
        env_info = envs_df[envs_df['environment_id'] == env_id].iloc[0]
        telemetry_df = self.data_loader.load_telemetry()
        env_telemetry = telemetry_df[telemetry_df['environment_id'] == env_id]
        
        return {
            "current_instance": env_info['current_instance_type'],
            "service_name": env_info['service_name'],
            "telemetry_count": len(env_telemetry),
            "telemetry_data": env_telemetry
        }, "Telemetry loaded successfully"

    def calculate_baseline(self, env_telemetry, current_inst):
        sim_res = self.simulator.run_simulation(env_telemetry, current_inst, current_inst)
        if not sim_res or 'baseline' not in sim_res:
            return None, "Baseline calculation failed"
            
        return sim_res['baseline'], "Baseline calculated successfully"

    def simulate_rightsizing(self, env_telemetry, current_inst, candidate_inst, target_latency=250, target_availability=99.9):
        sim_res = self.simulator.run_simulation(
            env_telemetry, current_inst, candidate_inst,
            latency_target=target_latency, availability_target=target_availability
        )
        return sim_res, "Simulation completed"

    def evaluate_safety(self, sim_res):
        decision, reasons = DecisionEngine.evaluate(sim_res)
        return {
            "decision": decision,
            "reasons": reasons
        }, "Safety evaluation completed"

    def inspect_infrastructure(self, env_id):
        state = self.infrastructure.get_instance_state(env_id)
        return {"current_state": state}, f"Infrastructure state is {state}"

    def execute_migration(self, env_id, candidate_inst):
        try:
            self.infrastructure.migrate_instance(env_id, candidate_inst)
            return True, f"Migrated {env_id} to {candidate_inst}"
        except Exception as e:
            return False, f"Migration execution failed: {str(e)}"

    def run_health_check(self, env_id, candidate_inst, sim_res, failure_mode="NORMAL"):
        """
        Simulates observing post-migration state.
        Allows deterministic injection of failures to test the agent's response.
        """
        if failure_mode == "NORMAL":
            return {"status": "HEALTHY", "observed_p95": sim_res['slo_eval']['projected_p95_latency'], "observed_cpu": sim_res['peak_cpu']}, "Health check passed"
        
        elif failure_mode == "CPU_FAILURE":
            return {"status": "DEGRADED", "observed_p95": sim_res['slo_eval']['projected_p95_latency'], "observed_cpu": 105.0}, "Health check failed: CPU Saturation"
            
        elif failure_mode == "MEMORY_FAILURE":
            return {"status": "DEGRADED", "observed_p95": sim_res['slo_eval']['projected_p95_latency'], "observed_cpu": sim_res['peak_cpu'], "observed_mem": 105.0}, "Health check failed: Memory Out of Bounds"
            
        elif failure_mode == "LATENCY_FAILURE":
            return {"status": "DEGRADED", "observed_p95": 800.0, "observed_cpu": sim_res['peak_cpu']}, "Health check failed: Latency SLO Violation"
            
        elif failure_mode == "AVAILABILITY_FAILURE":
            return {"status": "DEGRADED", "observed_p95": sim_res['slo_eval']['projected_p95_latency'], "observed_cpu": sim_res['peak_cpu'], "observed_availability": 98.0}, "Health check failed: Availability SLO Violation"
            
        return {"status": "UNKNOWN"}, "Unknown failure mode"

    def execute_rollback(self, env_id, original_inst):
        try:
            self.infrastructure.rollback_instance(env_id, original_inst)
            return True, f"Rolled back {env_id} to {original_inst}"
        except Exception as e:
            return False, f"Rollback failed: {str(e)}"

    def write_audit_event(self, env_id, current, candidate, event, reason=""):
        self.audit_log.record_event(env_id, current, candidate, event, reason)
        return True, "Audit event recorded"

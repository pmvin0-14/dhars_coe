from .simulator import Simulator
from .decision_engine import DecisionEngine
from .mock_infrastructure import LocalInfrastructure
from .audit_log import AuditLog

class MigrationOrchestrator:
    def __init__(self, simulator: Simulator, infrastructure: LocalInfrastructure, audit_log: AuditLog = None):
        self.simulator = simulator
        self.infrastructure = infrastructure
        self.audit_log = audit_log or AuditLog()
        self.state_tracking = {}

    def log_event(self, env_id, current, candidate, event, reason=""):
        self.audit_log.record_event(env_id, current, candidate, event, reason)

    def recommend_legacy_rightsizing(self, env_data, env_info):
        """
        Simulates the legacy workflow: if average CPU < 30%, recommend downsizing.
        """
        if env_data is None or len(env_data) == 0:
            return None, 0.0
            
        avg_cpu = env_data['cpu_utilization_pct'].mean()
        current_instance = env_info['current_instance_type']
        
        if avg_cpu < 30.0:
            if current_instance == 'large':
                return 'medium', avg_cpu
            elif current_instance == 'medium':
                return 'small', avg_cpu
                
        return None, avg_cpu

    def pre_migration_check(self, env_id, current_inst, candidate_inst, env_data, target_latency=250, target_availability=99.9, max_cpu=90, max_mem=90):
        """
        Validates whether a migration can safely proceed based on simulator results and infrastructure state.
        """
        self.log_event(env_id, current_inst, candidate_inst, "PRECHECK_STARTED")
        
        # 1. Check Infrastructure State
        valid, msg = self.infrastructure.validate_environment(env_id)
        if not valid:
            self.log_event(env_id, current_inst, candidate_inst, "PRECHECK_FAILED", msg)
            return False, msg, None

        actual_current = self.infrastructure.get_instance_state(env_id)
        if actual_current != current_inst:
            msg = f"Current instance mismatch: expected {current_inst}, got {actual_current}"
            self.log_event(env_id, current_inst, candidate_inst, "PRECHECK_FAILED", msg)
            return False, msg, None

        # 2. Run Simulation
        sim_res = self.simulator.run_simulation(
            env_data, current_inst, candidate_inst, 
            latency_target=target_latency, availability_target=target_availability
        )
        
        decision, reasons = DecisionEngine.evaluate(
            sim_res, max_safe_cpu=max_cpu, max_safe_mem=max_mem
        )
        
        if decision != "SAFE TO RIGHTSIZE":
            msg = f"Safety decision blocked migration: {decision}. Reasons: {reasons}"
            self.log_event(env_id, current_inst, candidate_inst, "MIGRATION_BLOCKED", msg)
            return False, msg, sim_res

        self.log_event(env_id, current_inst, candidate_inst, "MIGRATION_APPROVED", "Safety checks passed.")
        return True, "SAFE TO RIGHTSIZE", sim_res

    def execute_migration(self, env_id, current_inst, candidate_inst, simulate_post_migration_failure=False, sim_res=None):
        """
        Executes the migration on the mock infrastructure and runs a post-check.
        """
        self.log_event(env_id, current_inst, candidate_inst, "MIGRATION_STARTED")
        self.state_tracking[env_id] = {'status': 'MIGRATING', 'original': current_inst, 'candidate': candidate_inst}
        
        try:
            self.infrastructure.migrate_instance(env_id, candidate_inst)
            self.state_tracking[env_id]['status'] = 'MIGRATED'
            self.log_event(env_id, current_inst, candidate_inst, "MIGRATION_COMPLETED")
            
            # Post-migration check
            return self.post_migration_validation(env_id, current_inst, candidate_inst, sim_res, simulate_post_migration_failure)
            
        except Exception as e:
            self.log_event(env_id, current_inst, candidate_inst, "MIGRATION_FAILED", str(e))
            self.state_tracking[env_id]['status'] = 'FAILED'
            return False, f"Migration execution failed: {str(e)}"

    def post_migration_validation(self, env_id, current_inst, candidate_inst, sim_res, simulate_failure=False):
        """
        Runs post-migration validation checks. Injects failures if requested.
        Triggers rollback if validation fails.
        """
        self.log_event(env_id, current_inst, candidate_inst, "POSTCHECK_STARTED")
        
        # Simulate validation using the simulated results (representing post-migration metrics)
        # or artificially fail it for demonstration
        failed = False
        reason = ""
        
        if simulate_failure:
            failed = True
            reason = "Simulated failure injection triggered during post-check."
        elif sim_res:
            # Re-evaluate strict bounds as a secondary safeguard
            if sim_res['peak_cpu'] > 90:
                failed = True
                reason = f"Peak CPU ({sim_res['peak_cpu']}%) exceeded bounds post-migration."
            elif not sim_res['slo_eval']['latency_satisfied']:
                failed = True
                reason = "Latency SLO violated post-migration."
            elif not sim_res['slo_eval']['availability_satisfied']:
                failed = True
                reason = "Availability SLO violated post-migration."
        
        if failed:
            self.log_event(env_id, current_inst, candidate_inst, "POSTCHECK_FAILED", reason)
            return self.trigger_rollback(env_id, current_inst, candidate_inst, reason)
            
        self.log_event(env_id, current_inst, candidate_inst, "POSTCHECK_PASSED", "All post-migration checks satisfied.")
        self.state_tracking[env_id]['status'] = 'COMPLETED'
        return True, "Migration finalized successfully."

    def trigger_rollback(self, env_id, current_inst, candidate_inst, reason):
        """
        Rolls back the environment to the original instance.
        """
        self.log_event(env_id, current_inst, candidate_inst, "ROLLBACK_STARTED", reason)
        self.state_tracking[env_id]['status'] = 'ROLLING_BACK'
        
        try:
            self.infrastructure.rollback_instance(env_id, current_inst)
            self.state_tracking[env_id]['status'] = 'ROLLED_BACK'
            self.log_event(env_id, current_inst, candidate_inst, "ROLLBACK_COMPLETED", f"Rolled back to {current_inst}")
            return False, f"Rolled back due to: {reason}"
        except Exception as e:
            self.state_tracking[env_id]['status'] = 'ROLLBACK_FAILED'
            self.log_event(env_id, current_inst, candidate_inst, "ROLLBACK_FAILED", str(e))
            return False, f"Rollback failed: {str(e)}"

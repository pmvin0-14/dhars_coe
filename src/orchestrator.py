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

    def evaluate_all_candidates(self, env_id, current_inst, env_data, target_latency=250, target_availability=99.9, max_cpu=90, max_mem=90):
        """
        Evaluates all cheaper candidates and selects the best one according to safety and headroom.
        """
        if env_data is None or len(env_data) == 0:
            return "NO SAFE RIGHTSIZING OPTION", None, None

        catalog = self.simulator.catalog
        if current_inst not in catalog:
            return "NO SAFE RIGHTSIZING OPTION", None, None
            
        current_cost = catalog[current_inst]['base_price']
        
        candidates = []
        for inst, details in catalog.items():
            if details['base_price'] < current_cost:
                candidates.append(inst)
                
        if not candidates:
            return "NO SAFE RIGHTSIZING OPTION", None, None
            
        best_candidate = None
        best_sim_res = None
        best_headroom = -1
        
        for cand in candidates:
            sim_res = self.simulator.run_simulation(
                env_data, current_inst, cand, 
                latency_target=target_latency, availability_target=target_availability
            )
            decision, reasons = DecisionEngine.evaluate(sim_res, max_safe_cpu=max_cpu, max_safe_mem=max_mem)
            
            if decision == "SAFE TO RIGHTSIZE":
                # Calculate headroom
                headroom = min(100 - sim_res['peak_cpu'], 100 - sim_res['peak_mem'])
                
                # Priority: 1. Safety (checked), 2. Headroom, 3. Cost
                # We'll just maximize headroom for now among safe ones
                if headroom > best_headroom:
                    best_headroom = headroom
                    best_candidate = cand
                    best_sim_res = sim_res

        if best_candidate:
            return "SAFE TO RIGHTSIZE", best_candidate, best_sim_res
            
        return "NO SAFE RIGHTSIZING OPTION", None, None

    def recommend_legacy_rightsizing(self, env_data, env_info):
        """
        Simulates the legacy workflow: if average CPU < 30%, recommend downsizing.
        """
        if env_data is None or len(env_data) == 0:
            return None, 0.0
            
        avg_cpu = env_data['cpu_utilization_pct'].mean()
        current_instance = env_info['current_instance_type']
        
        if avg_cpu < 30.0:
            # Simple fallback legacy logic
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

    def execute_migration(self, env_id, current_inst, candidate_inst, sim_res=None, monitoring_scenario="stable"):
        """
        Executes the migration on the mock infrastructure and runs a post-check.
        """
        self.log_event(env_id, current_inst, candidate_inst, "MIGRATION_STARTED")
        self.state_tracking[env_id] = {'status': 'MIGRATING', 'original': current_inst, 'candidate': candidate_inst}
        
        try:
            self.infrastructure.migrate_instance(env_id, candidate_inst)
            self.state_tracking[env_id]['status'] = 'MIGRATED'
            self.log_event(env_id, current_inst, candidate_inst, "MIGRATION_EXECUTED")
            
            # Post-migration check
            return self.post_migration_validation(env_id, current_inst, candidate_inst, sim_res, monitoring_scenario)
            
        except Exception as e:
            self.log_event(env_id, current_inst, candidate_inst, "MIGRATION_FAILED", str(e))
            self.state_tracking[env_id]['status'] = 'FAILED'
            return False, f"Migration execution failed: {str(e)}"

    def post_migration_validation(self, env_id, current_inst, candidate_inst, sim_res, monitoring_scenario="stable"):
        """
        Runs post-migration validation checks via checkpoints.
        Triggers rollback if validation fails.
        """
        self.log_event(env_id, current_inst, candidate_inst, "MONITORING_STARTED")
        
        from .monitoring import PostMigrationMonitor
        monitor = PostMigrationMonitor()
        
        # Base observed metrics from simulation + small noise (if stable)
        base_metrics = {
            'cpu': sim_res['peak_cpu'] if sim_res else 50.0,
            'memory': sim_res['peak_mem'] if sim_res else 50.0,
            'latency': sim_res['slo_eval']['projected_p95_latency'] if sim_res else 50.0,
            'availability': sim_res['slo_eval']['projected_availability'] if sim_res else 100.0
        }
        
        checkpoints = monitor.run_monitoring_window(base_metrics, scenario=monitoring_scenario)
        final_health = monitor.evaluate_checkpoints(checkpoints)
        
        if final_health == "ROLLBACK_REQUIRED":
            self.log_event(env_id, current_inst, candidate_inst, "FAILURE_DETECTED", "Monitoring deemed environment unhealthy.")
            self.log_event(env_id, current_inst, candidate_inst, "MIGRATION_STOPPED")
            return self.trigger_rollback(env_id, current_inst, candidate_inst, "Post-migration monitoring failed.")
            
        self.log_event(env_id, current_inst, candidate_inst, "POSTCHECK_PASSED", "All post-migration checkpoints satisfied.")
        self.state_tracking[env_id]['status'] = 'COMPLETED'
        
        # Log prediction accuracy for the last checkpoint
        from .observation_model import ObservationModel
        if sim_res:
            acc = ObservationModel.compare_metrics(sim_res, checkpoints[-1])
            self.log_event(env_id, current_inst, candidate_inst, "PREDICTION_ACCURACY", str(acc))
            
        return True, "Migration finalized successfully."

    def trigger_rollback(self, env_id, current_inst, candidate_inst, reason):
        """
        Rolls back the environment to the original instance.
        """
        self.log_event(env_id, current_inst, candidate_inst, "ROLLBACK_STARTED", reason)
        self.state_tracking[env_id]['status'] = 'ROLLING_BACK'
        
        try:
            self.infrastructure.rollback_instance(env_id, current_inst)
            
            # Verify restoration
            actual_current = self.infrastructure.get_instance_state(env_id)
            if actual_current != current_inst:
                raise Exception(f"Restoration verification failed. Expected {current_inst}, got {actual_current}")
                
            self.state_tracking[env_id]['status'] = 'ROLLED_BACK'
            self.log_event(env_id, current_inst, candidate_inst, "ORIGINAL_CONFIGURATION_RESTORED")
            self.log_event(env_id, current_inst, candidate_inst, "RESTORATION_VERIFIED", f"Rolled back to {current_inst}")
            return False, f"Rolled back due to: {reason}"
        except Exception as e:
            self.state_tracking[env_id]['status'] = 'FAILED'
            self.log_event(env_id, current_inst, candidate_inst, "ROLLBACK_FAILED", str(e))
            return False, f"Rollback failed: {str(e)}"

import copy
from src.agent_tools import AgentTools

class RightsizingAgent:
    STATES = [
        "OBSERVING", "ANALYZING", "PLANNING", "VALIDATING", "APPROVED", 
        "EXECUTING", "VERIFYING", "COMPLETED", "ROLLING_BACK", "ROLLED_BACK", 
        "BLOCKED", "FAILED"
    ]

    def __init__(self, tools: AgentTools):
        self.tools = tools
        self.state = "OBSERVING"
        self.trace = []
        self.env_id = None
        self.candidate = None
        self.risk_level = "UNKNOWN"
        self.failure_mode = "NORMAL"

    def _record_trace(self, step, state, action, result, details=None):
        entry = {
            "step": step,
            "state": state,
            "action": action,
            "result": result
        }
        if details:
            entry["details"] = details
        self.trace.append(entry)

    def evaluate_risk(self, sim_res):
        if not sim_res:
            return "UNKNOWN"
            
        peak_cpu = sim_res.get('peak_cpu', 0)
        slo = sim_res.get('slo_eval', {})
        latency_sat = slo.get('latency_satisfied', False)
        avail_sat = slo.get('availability_satisfied', False)
        
        if not latency_sat or not avail_sat or peak_cpu > 90:
            return "CRITICAL"
        elif peak_cpu > 80:
            return "HIGH"
        elif peak_cpu > 60:
            return "MEDIUM"
        else:
            return "LOW"

    def run_lifecycle(self, env_id, candidate, failure_mode="NORMAL"):
        """
        Executes the autonomous agent workflow. 
        State transitions:
        OBSERVE -> ANALYZE -> PLAN -> VALIDATING -> EXECUTING -> VERIFYING -> RE-PLAN (ROLLBACK) / COMPLETED
        
        This loop mimics an SRE investigating a rightsizing opportunity, performing local safety checks,
        executing a mock infrastructure transition, checking post-migration health, and automatically
        rolling back if degradation is observed.
        """
        self.state = "OBSERVING"
        self.env_id = env_id
        self.candidate = candidate
        self.failure_mode = failure_mode
        self.trace = []
        
        step = 1
        
        # 1. OBSERVE
        self._record_trace(step, self.state, "load_telemetry", f"Loaded telemetry for {env_id}")
        telemetry_info, msg = self.tools.load_telemetry(env_id)
        if not telemetry_info:
            self.state = "FAILED"
            self._record_trace(step, self.state, "abort", "Telemetry load failed")
            return self.trace
        
        current_inst = telemetry_info['current_instance']
        env_telemetry = telemetry_info['telemetry_data']
        step += 1
        
        # 2. ANALYZE
        self.state = "ANALYZING"
        baseline, msg = self.tools.calculate_baseline(env_telemetry, current_inst)
        self._record_trace(step, self.state, "calculate_baseline", f"Current instance: {current_inst}", {"average_cpu": baseline.get('avg_cpu', 0)})
        step += 1
        
        # 3. PLAN
        self.state = "PLANNING"
        self._record_trace(step, self.state, "select_candidate", f"Candidate: {self.candidate}")
        step += 1
        
        # 4. SIMULATE
        sim_res, msg = self.tools.simulate_rightsizing(env_telemetry, current_inst, self.candidate)
        cost_saving = sim_res['cost_eval'].get('absolute_monthly_saving', 0) if sim_res else 0
        self._record_trace(step, "SIMULATING", "simulate_rightsizing", f"Projected cost saving: ${cost_saving:.2f}/mo")
        step += 1
        
        # 5. VALIDATING (SAFETY CHECK)
        self.state = "VALIDATING"
        safety, msg = self.tools.evaluate_safety(sim_res)
        self.risk_level = self.evaluate_risk(sim_res)
        
        details = {
            "Peak CPU": f"{sim_res.get('peak_cpu', 0):.1f}%",
            "Peak Memory": f"{sim_res.get('peak_mem', 0):.1f}%",
            "Latency Satisfied": sim_res.get('slo_eval', {}).get('latency_satisfied'),
            "Risk Level": self.risk_level
        }
        self._record_trace(step, self.state, "evaluate_safety", safety['decision'], details)
        
        self.tools.write_audit_event(env_id, current_inst, self.candidate, "AGENT_VALIDATING", safety['decision'])
        step += 1
        
        # 6. DECIDE
        if safety['decision'] != "SAFE TO RIGHTSIZE":
            self.state = "BLOCKED"
            self._record_trace(step, "DECIDE", "block_migration", "Migration blocked by safety engine", {"reasons": safety['reasons']})
            self.tools.write_audit_event(env_id, current_inst, self.candidate, "AGENT_BLOCKED", str(safety['reasons']))
            return self.trace
            
        self.state = "APPROVED"
        self._record_trace(step, "DECIDE", "approve_migration", "SAFE TO RIGHTSIZE")
        self.tools.write_audit_event(env_id, current_inst, self.candidate, "AGENT_APPROVED")
        step += 1
        
        # 7. ACT (EXECUTE)
        self.state = "EXECUTING"
        success, exec_msg = self.tools.execute_migration(env_id, self.candidate)
        self._record_trace(step, self.state, "execute_local_migration", "Executed local migration" if success else exec_msg)
        self.tools.write_audit_event(env_id, current_inst, self.candidate, "AGENT_EXECUTED")
        if not success:
            self.state = "FAILED"
            return self.trace
        step += 1
        
        # 8. VERIFY (RE-OBSERVE)
        self.state = "VERIFYING"
        health, msg = self.tools.run_health_check(env_id, self.candidate, sim_res, self.failure_mode)
        self._record_trace(step, self.state, "run_health_check", f"Post-migration health: {health['status']}", health)
        self.tools.write_audit_event(env_id, current_inst, self.candidate, "AGENT_VERIFYING", health['status'])
        step += 1
        
        # 9. RE-PLAN / FINALIZE
        if health['status'] != "HEALTHY":
            self.state = "ROLLING_BACK"
            self._record_trace(step, "RE_PLAN", "plan_rollback", "Health check failed, planning rollback")
            step += 1
            
            success, r_msg = self.tools.execute_rollback(env_id, current_inst)
            self.state = "ROLLED_BACK"
            self._record_trace(step, self.state, "execute_rollback", "Original instance restored")
            self.tools.write_audit_event(env_id, current_inst, self.candidate, "AGENT_ROLLED_BACK")
        else:
            self.state = "COMPLETED"
            self._record_trace(step, "FINALIZE", "retain_migration", "Migration retained")
            self.tools.write_audit_event(env_id, current_inst, self.candidate, "AGENT_COMPLETED")
            
        return self.trace

    def analyze_portfolio(self, environments):
        """Analyze a list of environments and return ranked recommendations."""
        results = []
        for env_id in environments:
            telemetry_info, _ = self.tools.load_telemetry(env_id)
            if not telemetry_info:
                continue
                
            current_inst = telemetry_info['current_instance']
            env_telemetry = telemetry_info['telemetry_data']
            
            if current_inst == "large":
                candidate = "medium"
            elif current_inst == "medium":
                candidate = "small"
            else:
                continue # Skip small instances as they cannot be downsized further
                
            sim_res, _ = self.tools.simulate_rightsizing(env_telemetry, current_inst, candidate)
            safety, _ = self.tools.evaluate_safety(sim_res)
            risk = self.evaluate_risk(sim_res)
            
            cost_saving = sim_res['cost_eval'].get('absolute_monthly_saving', 0) if sim_res else 0
            
            results.append({
                "environment_id": env_id,
                "current": current_inst,
                "candidate": candidate,
                "safety_decision": safety['decision'],
                "risk_level": risk,
                "cost_saving": cost_saving
            })
            
        safe_envs = [r for r in results if r['safety_decision'] == "SAFE TO RIGHTSIZE"]
        blocked_envs = [r for r in results if r['safety_decision'] != "SAFE TO RIGHTSIZE"]
        
        safe_envs.sort(key=lambda x: x['cost_saving'], reverse=True)
        blocked_envs.sort(key=lambda x: x['cost_saving'], reverse=True)
        
        return safe_envs, blocked_envs

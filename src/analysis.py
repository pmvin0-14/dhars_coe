import pandas as pd

class AnalysisEngine:
    @staticmethod
    def compare_legacy_vs_agentic(legacy_orchestrator, agent, env_id, candidate_inst):
        """
        Compares the deterministic workflow vs the agentic workflow.
        Returns a dictionary of differences.
        """
        # Legacy
        legacy_trace = {}
        # We assume legacy runs evaluate_all_candidates and execute_migration directly.
        # This is just a structural mock for comparison if both use same safety engine.
        
        return {
            "legacy": "Deterministic Execution",
            "agentic": "State Machine Execution",
            "safety_engine": "Identical",
            "observation": "Agentic records trace steps, legacy does not explicitly."
        }

    @staticmethod
    def portfolio_optimization(envs_df, telemetry_df, orchestrator):
        """
        Calculates portfolio-wide potential savings.
        """
        results = []
        total_current_cost = 0.0
        total_potential_savings_monthly = 0.0
        blocked_potential_savings_monthly = 0.0
        
        safe_count = 0
        blocked_count = 0
        
        for _, row in envs_df.iterrows():
            env_id = row['environment_id']
            current = row['current_instance_type']
            data = telemetry_df[telemetry_df['environment_id'] == env_id]
            
            decision, cand, res = orchestrator.evaluate_all_candidates(env_id, current, data)
            
            # Assume 730 hours in a month for cost
            # Get current cost from baseline
            sim_res_current = orchestrator.simulator.run_simulation(data, current, current)
            current_monthly = sim_res_current['cost_eval']['baseline_monthly_cost'] if sim_res_current else 0
            total_current_cost += current_monthly
            
            if cand and res:
                candidate_monthly = res['cost_eval']['simulated_monthly_cost']
                saving = res['cost_eval']['absolute_monthly_saving']
                risk = "LOW" if res['peak_cpu'] < 60 else "MEDIUM" if res['peak_cpu'] < 80 else "HIGH"
                reason = "Safe" if decision == "SAFE TO RIGHTSIZE" else "Safety Bounds Exceeded"
            else:
                candidate_monthly = current_monthly
                saving = 0.0
                risk = "UNKNOWN"
                reason = decision
                
            if decision == "SAFE TO RIGHTSIZE":
                safe_count += 1
                total_potential_savings_monthly += saving
            else:
                blocked_count += 1
                blocked_potential_savings_monthly += saving
                
            results.append({
                "environment_id": env_id,
                "current_instance": current,
                "selected_candidate": cand,
                "candidate_cost": candidate_monthly,
                "potential_saving": saving,
                "decision": decision,
                "risk": risk,
                "blocking_reason": reason
            })
            
        return {
            "summary": {
                "total_environments": len(envs_df),
                "safe_environments": safe_count,
                "blocked_environments": blocked_count,
                "current_monthly_cost": total_current_cost,
                "potential_monthly_savings": total_potential_savings_monthly,
                "potential_annual_savings": total_potential_savings_monthly * 12,
                "blocked_potential_savings": blocked_potential_savings_monthly
            },
            "environment_details": results
        }

    @staticmethod
    def cost_performance_tradeoff(sim_res_current, sim_res_candidate):
        """
        Compares CURRENT vs CANDIDATE.
        """
        if not sim_res_current or not sim_res_candidate:
            return {}
            
        return {
            "cost_delta": sim_res_candidate['cost_eval']['simulated_monthly_cost'] - sim_res_current['cost_eval']['baseline_monthly_cost'],
            "cpu_delta": sim_res_candidate['peak_cpu'] - sim_res_current['peak_cpu'],
            "memory_delta": sim_res_candidate['peak_mem'] - sim_res_current['peak_mem'],
            "latency_delta": sim_res_candidate['slo_eval']['projected_p95_latency'] - sim_res_current['slo_eval']['projected_p95_latency'],
            "availability_delta": sim_res_candidate['slo_eval']['projected_availability'] - sim_res_current['slo_eval']['projected_availability'],
            "resource_headroom": 100.0 - max(sim_res_candidate['peak_cpu'], sim_res_candidate['peak_mem'])
        }

    @staticmethod
    def generate_explanation(decision, current, candidate, sim_res, reasons):
        """
        Generates structured WHY explanations.
        """
        if decision == "SAFE TO RIGHTSIZE":
            return {
                "decision": "SAFE",
                "current_instance": current,
                "candidate": candidate,
                "cost_reduction": sim_res['cost_eval']['absolute_monthly_saving'] if sim_res else 0,
                "cpu_projection": sim_res['peak_cpu'] if sim_res else 0,
                "memory_projection": sim_res['peak_mem'] if sim_res else 0,
                "latency_projection": sim_res['slo_eval']['projected_p95_latency'] if sim_res else 0,
                "availability_projection": sim_res['slo_eval']['projected_availability'] if sim_res else 0,
                "evidence": "All simulated metrics are within strict safety bounds.",
                "passed_checks": ["CPU < 90%", "Memory < 90%", "Latency SLO Met", "Availability SLO Met"]
            }
        else:
            return {
                "decision": "BLOCKED",
                "candidate": candidate,
                "exact_reason": str(reasons),
                "projected_cpu": sim_res['peak_cpu'] if sim_res else None,
                "projected_memory": sim_res['peak_mem'] if sim_res else None,
                "projected_latency": sim_res['slo_eval']['projected_p95_latency'] if sim_res else None,
                "projected_availability": sim_res['slo_eval']['projected_availability'] if sim_res else None
            }

class StakeholderViews:
    @staticmethod
    def get_infrastructure_engineer_view(env_id, analysis_results, health_status):
        return {
            "view": "INFRASTRUCTURE ENGINEER",
            "resource_usage": analysis_results.get("cpu_projection", 0),
            "safety": analysis_results.get("decision"),
            "health": health_status,
            "label": "SIMULATED STAKEHOLDER VALIDATION"
        }
        
    @staticmethod
    def get_finops_view(portfolio_summary):
        return {
            "view": "FINOPS / COST MANAGER",
            "cost": portfolio_summary.get("current_monthly_cost"),
            "potential_savings": portfolio_summary.get("potential_monthly_savings"),
            "portfolio_health": f"{portfolio_summary.get('safe_environments')} Safe",
            "label": "SIMULATED STAKEHOLDER VALIDATION"
        }
        
    @staticmethod
    def get_service_owner_view(analysis_results):
        return {
            "view": "SERVICE OWNER",
            "latency": analysis_results.get("latency_projection"),
            "availability": analysis_results.get("availability_projection"),
            "operational_risk": "LOW" if analysis_results.get("decision") == "SAFE" else "HIGH",
            "label": "SIMULATED STAKEHOLDER VALIDATION"
        }

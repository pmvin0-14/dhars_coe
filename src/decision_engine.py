class DecisionEngine:
    @staticmethod
    def evaluate(simulation_results, data_quality="HIGH", max_safe_cpu=90, max_safe_mem=90):
        if simulation_results is None:
            return "INSUFFICIENT DATA", ["No telemetry available for simulation."]
            
        if data_quality == "LOW":
            return "INSUFFICIENT DATA", ["Data quality is too low to safely recommend rightsizing."]
            
        reasons = []
        decision = "SAFE TO RIGHTSIZE"
        
        slo_eval = simulation_results['slo_eval']
        cost_eval = simulation_results['cost_eval']
        
        if cost_eval['absolute_monthly_saving'] <= 0:
            decision = "DO NOT RIGHTSIZE"
            reasons.append("Candidate does not provide cost benefit.")
            
        if not slo_eval['latency_satisfied']:
            decision = "DO NOT RIGHTSIZE"
            reasons.append(f"Projected P95 latency = {slo_eval['projected_p95_latency']:.2f} ms (Target violated)")
            
        if not slo_eval['availability_satisfied']:
            decision = "DO NOT RIGHTSIZE"
            reasons.append(f"Projected availability = {slo_eval['projected_availability']:.2f}% (Target violated)")
            
        if simulation_results['peak_cpu'] > max_safe_cpu:
            decision = "DO NOT RIGHTSIZE"
            reasons.append(f"Projected peak CPU = {simulation_results['peak_cpu']:.1f}% exceeds safe limit ({max_safe_cpu}%)")
            
        if simulation_results['peak_mem'] > max_safe_mem:
            decision = "DO NOT RIGHTSIZE"
            reasons.append(f"Projected peak memory = {simulation_results['peak_mem']:.1f}% exceeds safe limit ({max_safe_mem}%)")
            
        if decision == "SAFE TO RIGHTSIZE":
            reasons.append("Cost decreases while SLO targets and resource limits remain satisfied.")
            
        return decision, reasons

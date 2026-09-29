from .simulator import Simulator

class SensitivityAnalyzer:
    def __init__(self, simulator):
        self.simulator = simulator
        
    def analyze_traffic_growth(self, env_data, current_instance, candidate_instance, 
                               latency_target=250, availability_target=99.9,
                               growth_levels=[0.0, 0.1, 0.2, 0.3, 0.4]):
        """
        Runs the simulation across different traffic growth assumptions.
        Returns a summary of decisions at each growth level.
        """
        from .decision_engine import DecisionEngine
        
        results = []
        for growth in growth_levels:
            sim_result = self.simulator.run_simulation(
                env_data, current_instance, candidate_instance,
                latency_target, availability_target, traffic_growth=growth
            )
            
            if sim_result is None:
                continue
                
            decision, reasons = DecisionEngine.evaluate(sim_result)
            
            results.append({
                'traffic_growth_pct': growth * 100,
                'decision': decision,
                'p95_latency': sim_result['slo_eval']['projected_p95_latency'],
                'availability': sim_result['slo_eval']['projected_availability'],
                'cost_saving': sim_result['cost_eval']['absolute_monthly_saving'],
                'reasons': reasons
            })
            
        return results
    def analyze_advanced_sensitivity(self, env_data, current_instance, candidate_instance, 
                                   latency_target=250, availability_target=99.9,
                                   variations=None):
        """
        Runs sensitivity analysis against variations (growth, CPU pressure, memory pressure).
        """
        from .decision_engine import DecisionEngine
        if variations is None:
            variations = [
                {'traffic_growth': 0.1, 'cpu_pressure': 0.0, 'memory_pressure': 0.0},
                {'traffic_growth': 0.0, 'cpu_pressure': 0.1, 'memory_pressure': 0.0},
                {'traffic_growth': 0.0, 'cpu_pressure': 0.0, 'memory_pressure': 0.1}
            ]
            
        results = []
        for var in variations:
            growth = var.get('traffic_growth', 0.0)
            cpu_p = var.get('cpu_pressure', 0.0)
            mem_p = var.get('memory_pressure', 0.0)
            lat_t = var.get('latency_target', latency_target)
            avail_t = var.get('availability_target', availability_target)
            
            sim_result = self.simulator.run_simulation(
                env_data, current_instance, candidate_instance,
                lat_t, avail_t, traffic_growth=growth, cpu_pressure=cpu_p, memory_pressure=mem_p
            )
            
            if sim_result is None:
                continue
                
            decision, reasons = DecisionEngine.evaluate(sim_result)
            
            results.append({
                'variation': var,
                'decision': decision,
                'p95_latency': sim_result['slo_eval']['projected_p95_latency'],
                'availability': sim_result['slo_eval']['projected_availability'],
                'reasons': reasons
            })
            
        return results

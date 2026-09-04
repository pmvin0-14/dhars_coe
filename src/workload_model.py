import numpy as np

class WorkloadModel:
    def __init__(self, instance_catalog):
        self.catalog = instance_catalog

    def project_workload(self, telemetry_df, current_instance, candidate_instance, traffic_growth=0.0):
        """
        Projects resource pressure on a candidate instance given the historical telemetry.
        traffic_growth is a float (e.g., 0.1 for 10% growth).
        """
        # Get capacity factors
        current_vcpu = self.catalog[current_instance]['vcpu']
        current_mem = self.catalog[current_instance]['memory_gb']
        
        candidate_vcpu = self.catalog[candidate_instance]['vcpu']
        candidate_mem = self.catalog[candidate_instance]['memory_gb']
        
        # Calculate ratio of capacities
        cpu_ratio = current_vcpu / candidate_vcpu
        mem_ratio = current_mem / candidate_mem
        
        # Project new utilization based on historical, applying growth
        growth_factor = 1.0 + traffic_growth
        
        projected = telemetry_df.copy()
        
        projected['projected_cpu'] = (projected['cpu_utilization_pct'] * cpu_ratio * growth_factor)
        projected['projected_memory'] = (projected['memory_utilization_pct'] * mem_ratio * growth_factor)
        
        # Hard cap at some theoretical max, but values > 100 indicate severe saturation
        # We don't clip at 100 because we need to know how badly saturated it is for latency penalties
        
        return projected

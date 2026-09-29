import numpy as np
import pandas as pd

class WorkloadModel:
    def __init__(self, instance_catalog):
        self.catalog = instance_catalog

    def project_workload(self, telemetry_df, current_instance, candidate_instance, 
                         traffic_growth=0.0, profile='steady', 
                         cpu_pressure=0.0, memory_pressure=0.0):
        """
        Projects resource pressure on a candidate instance given the historical telemetry.
        traffic_growth: float (e.g., 0.1 for 10% growth).
        profile: 'steady', 'peak', 'bursty', 'low-traffic', 'seasonal'
        cpu_pressure: float to artificially inflate CPU (e.g. 0.2 for 20% increase)
        memory_pressure: float to artificially inflate Memory
        """
        if telemetry_df is None or len(telemetry_df) == 0:
            return pd.DataFrame()

        current_vcpu = self.catalog[current_instance]['vcpu']
        current_mem = self.catalog[current_instance]['memory_gb']
        
        candidate_vcpu = self.catalog[candidate_instance]['vcpu']
        candidate_mem = self.catalog[candidate_instance]['memory_gb']
        
        cpu_ratio = current_vcpu / candidate_vcpu
        mem_ratio = current_mem / candidate_mem
        
        growth_factor = 1.0 + traffic_growth
        projected = telemetry_df.copy()
        
        # Apply profile transformations
        if profile == 'peak':
            # Increase top 10% of values by 50%
            p90_req = projected['request_volume'].quantile(0.9)
            peak_mask = projected['request_volume'] >= p90_req
            projected.loc[peak_mask, 'request_volume'] *= 1.5
        elif profile == 'bursty':
            # Random occasional spikes (deterministic by setting seed based on first timestamp)
            if not projected.empty:
                np.random.seed(int(projected['timestamp'].iloc[0].timestamp()))
                spike_indices = np.random.choice(len(projected), size=max(1, int(len(projected)*0.05)), replace=False)
                projected.iloc[spike_indices, projected.columns.get_loc('request_volume')] *= 3.0
        elif profile == 'low-traffic':
            projected['request_volume'] *= 0.5
        elif profile == 'seasonal':
            # Add sine wave based on index
            hours = np.arange(len(projected))
            seasonal_factor = 1.0 + 0.3 * np.sin(2 * np.pi * hours / 24.0)
            projected['request_volume'] *= seasonal_factor
            
        # Apply growth
        projected['request_volume'] *= growth_factor

        # Project CPU and Memory
        req_ratio = projected['request_volume'] / telemetry_df['request_volume'].replace(0, 1)
        
        base_cpu = projected['cpu_utilization_pct'] * cpu_ratio * req_ratio
        base_mem = projected['memory_utilization_pct'] * mem_ratio * req_ratio

        projected['projected_cpu'] = base_cpu * (1.0 + cpu_pressure)
        projected['projected_memory'] = base_mem * (1.0 + memory_pressure)
        
        return projected


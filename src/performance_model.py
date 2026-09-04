import numpy as np

class PerformanceModel:
    @staticmethod
    def project_performance(projected_df):
        """
        WORKLOAD-AWARE SIMULATION MODEL
        
        This model mathematically projects latency and availability based on resource pressure.
        It is designed to be transparent and explainable for academic evaluation.
        
        Assumptions:
        1. Base expected latency is 50ms without resource saturation.
        2. Resource pressure is the maximum of CPU or Memory utilization.
        3. Below a safe threshold (75%), latency increases minimally.
        4. Above the safe threshold, a non-linear penalty is applied due to queuing.
        5. Above a saturation limit (100%), a severe penalty is applied, indicating SLO risk.
        6. Availability degrades linearly once resources exceed 95%.
        """
        df = projected_df.copy()
        
        cpu_util = df['projected_cpu']
        mem_util = df['projected_memory']
        
        # We assume a fixed base latency for the service.
        base_latency = 50.0
        
        # Resource pressure is dictated by the most constrained resource
        resource_pressure = np.maximum(cpu_util, mem_util)
        
        safe_threshold = 75.0
        saturation_limit = 100.0
        
        penalty = np.zeros(len(df))
        
        # 1. Moderate pressure (<= 75%): small latency penalty
        mask_safe = resource_pressure <= safe_threshold
        penalty[mask_safe] = (resource_pressure[mask_safe] / safe_threshold) * 5.0
        
        # 2. High pressure (> 75% but < 100%): non-linear queuing penalty
        mask_high = (resource_pressure > safe_threshold) & (resource_pressure < saturation_limit)
        penalty[mask_high] = 5.0 + ((resource_pressure[mask_high] - safe_threshold) ** 1.5)
        
        # 3. Saturation (>= 100%): severe latency penalty
        mask_sat = resource_pressure >= saturation_limit
        penalty[mask_sat] = 100.0 + ((resource_pressure[mask_sat] - saturation_limit) ** 2.0)
        
        df['projected_latency'] = base_latency + penalty
        
        # Availability model: degrades when resources exceed 95%
        # The system remains conservative, maintaining 100% unless severe pressure occurs.
        availability = np.ones(len(df)) * 100.0
        avail_fail_mask = resource_pressure > 95.0
        availability[avail_fail_mask] = 100.0 - (resource_pressure[avail_fail_mask] - 95.0) * 0.5
        
        df['projected_availability'] = np.clip(availability, 0.0, 100.0)
        
        return df

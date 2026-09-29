from .workload_model import WorkloadModel
from .performance_model import PerformanceModel
from .cost_model import CostModel
from .availability_model import AvailabilityModel
from .baseline import BaselineEngine
import numpy as np

class Simulator:
    def __init__(self, instance_catalog, pricing_df):
        self.catalog = instance_catalog
        self.pricing_df = pricing_df
        self.workload_model = WorkloadModel(instance_catalog)
        self.perf_model = PerformanceModel()

    def run_simulation(self, env_data, current_instance, candidate_instance, 
                       latency_target=250, availability_target=99.9, traffic_growth=0.0,
                       profile='steady', cpu_pressure=0.0, memory_pressure=0.0):
        """
        Runs the full simulation pipeline for a candidate instance.
        """
        if env_data is None or len(env_data) == 0:
            return None
            
        # 1. Baseline
        baseline_metrics = BaselineEngine.calculate_baseline(env_data, env_data['environment_id'].iloc[0])
        
        # 2. Workload Projection
        projected_workload = self.workload_model.project_workload(
            env_data, current_instance, candidate_instance, 
            traffic_growth=traffic_growth, profile=profile, 
            cpu_pressure=cpu_pressure, memory_pressure=memory_pressure
        )
        
        # 3. Performance Projection
        projected_performance = self.perf_model.project_performance(projected_workload)
        
        # 4. SLO Evaluation
        slo_eval = AvailabilityModel.evaluate_slo(
            projected_performance, latency_target, availability_target
        )
        
        # 5. Cost Calculation
        cost_eval = CostModel.calculate_costs(
            self.pricing_df, current_instance, candidate_instance, hours=len(env_data)
        )
        
        # Resource Pressure
        peak_cpu = projected_performance['projected_cpu'].max()
        peak_mem = projected_performance['projected_memory'].max()
        
        return {
            'baseline': baseline_metrics,
            'projected_performance': projected_performance, # full df
            'slo_eval': slo_eval,
            'cost_eval': cost_eval,
            'peak_cpu': peak_cpu,
            'peak_mem': peak_mem
        }

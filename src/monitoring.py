import pandas as pd
import numpy as np

class PostMigrationMonitor:
    def __init__(self, target_latency=250, target_availability=99.9, max_cpu=90, max_mem=90):
        self.target_latency = target_latency
        self.target_availability = target_availability
        self.max_cpu = max_cpu
        self.max_mem = max_mem

    def _determine_health(self, metrics):
        if metrics['cpu'] > self.max_cpu or metrics['memory'] > self.max_mem:
            return "ROLLBACK_REQUIRED"
        if metrics['latency'] > self.target_latency or metrics['availability'] < self.target_availability:
            return "DEGRADED"
        if metrics['cpu'] > self.max_cpu - 10 or metrics['memory'] > self.max_mem - 10:
            return "DEGRADED"
        return "STABLE"

    def run_monitoring_window(self, base_metrics, scenario="stable"):
        """
        Simulates 5 monitoring checkpoints (T+0 to T+4).
        scenario can be: "stable", "gradual_degradation", "immediate_degradation", "recovery", "persistent_failure"
        """
        checkpoints = []
        current_metrics = base_metrics.copy()
        
        for t in range(5):
            if scenario == "stable":
                noise = np.random.normal(0, 2)
                current_metrics['cpu'] = max(1, min(100, base_metrics['cpu'] + noise))
                current_metrics['memory'] = max(1, min(100, base_metrics['memory'] + noise))
                
            elif scenario == "gradual_degradation":
                current_metrics['cpu'] = min(100, base_metrics['cpu'] + (t * 10))
                current_metrics['latency'] = base_metrics['latency'] + (t * 50)
                
            elif scenario == "immediate_degradation":
                if t > 0:
                    current_metrics['cpu'] = 95.0
                    current_metrics['latency'] = 500.0
                    
            elif scenario == "recovery":
                if t == 1:
                    current_metrics['cpu'] = 95.0 # spike
                else:
                    current_metrics['cpu'] = base_metrics['cpu']
                    
            elif scenario == "persistent_failure":
                current_metrics['availability'] = 95.0 # hard failure
                
            health = self._determine_health(current_metrics)
            
            checkpoints.append({
                "checkpoint": f"T+{t}",
                "cpu": current_metrics['cpu'],
                "memory": current_metrics['memory'],
                "latency": current_metrics['latency'],
                "availability": current_metrics['availability'],
                "health_status": health
            })
            
        return checkpoints

    def evaluate_checkpoints(self, checkpoints):
        """
        Determines final action based on checkpoint history.
        """
        statuses = [c['health_status'] for c in checkpoints]
        if "ROLLBACK_REQUIRED" in statuses:
            return "ROLLBACK_REQUIRED"
        if statuses.count("DEGRADED") > 2:
            return "ROLLBACK_REQUIRED" # Sustained degradation
        return "STABLE"

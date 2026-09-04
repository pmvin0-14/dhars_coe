import numpy as np

class BaselineEngine:
    @staticmethod
    def calculate_baseline(telemetry_df, env_id):
        env_data = telemetry_df[telemetry_df['environment_id'] == env_id]
        
        if env_data.empty:
            return None
            
        metrics = {}
        
        # CPU
        metrics['mean_cpu'] = env_data['cpu_utilization_pct'].mean()
        metrics['median_cpu'] = env_data['cpu_utilization_pct'].median()
        metrics['p95_cpu'] = np.percentile(env_data['cpu_utilization_pct'].dropna(), 95)
        metrics['peak_cpu'] = env_data['cpu_utilization_pct'].max()
        
        # Memory
        metrics['mean_memory'] = env_data['memory_utilization_pct'].mean()
        metrics['p95_memory'] = np.percentile(env_data['memory_utilization_pct'].dropna(), 95)
        metrics['peak_memory'] = env_data['memory_utilization_pct'].max()
        
        # Traffic
        metrics['mean_request_volume'] = env_data['request_volume'].mean()
        metrics['p95_request_volume'] = np.percentile(env_data['request_volume'].dropna(), 95)
        metrics['peak_request_volume'] = env_data['request_volume'].max()
        
        # Performance
        metrics['mean_latency'] = env_data['latency_ms'].mean()
        metrics['p95_latency'] = np.percentile(env_data['latency_ms'].dropna(), 95)
        metrics['p99_latency'] = np.percentile(env_data['latency_ms'].dropna(), 99)
        
        # Reliability
        metrics['measured_availability'] = env_data['availability_pct'].mean()
        # SLO violation: availability < 99.9%
        metrics['slo_violations'] = len(env_data[env_data['availability_pct'] < 99.9])
        
        return metrics

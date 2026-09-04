import numpy as np

class AvailabilityModel:
    @staticmethod
    def evaluate_slo(projected_df, latency_target, availability_target):
        """
        Evaluates the projected performance against SLO targets.
        """
        p95_latency = np.percentile(projected_df['projected_latency'].dropna(), 95)
        mean_availability = projected_df['projected_availability'].mean()
        
        slo_violations = len(projected_df[projected_df['projected_availability'] < availability_target])
        
        latency_satisfied = p95_latency <= latency_target
        availability_satisfied = mean_availability >= availability_target
        
        return {
            'projected_p95_latency': p95_latency,
            'projected_availability': mean_availability,
            'slo_violation_rate': slo_violations / len(projected_df) if len(projected_df) > 0 else 0,
            'latency_satisfied': latency_satisfied,
            'availability_satisfied': availability_satisfied
        }

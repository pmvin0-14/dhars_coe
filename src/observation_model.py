import pandas as pd
import numpy as np

class ObservationModel:
    @staticmethod
    def calculate_accuracy(predicted, observed):
        """
        Calculates prediction accuracy for a single metric.
        """
        if observed == 0 and predicted == 0:
            abs_err = 0.0
            pct_err = 0.0
        elif observed == 0:
            abs_err = abs(predicted - observed)
            pct_err = 100.0 # Arbitrary for 0 denominator
        else:
            abs_err = abs(predicted - observed)
            pct_err = (abs_err / observed) * 100.0
            
        return {
            "predicted": predicted,
            "observed": observed,
            "absolute_error": abs_err,
            "percentage_error": pct_err
        }

    @staticmethod
    def compare_metrics(predicted_sim_res, observed_metrics):
        """
        Compares predicted performance metrics with observed post-migration metrics.
        """
        pred_cpu = predicted_sim_res.get('peak_cpu', 0)
        obs_cpu = observed_metrics.get('cpu', 0)
        
        pred_mem = predicted_sim_res.get('peak_mem', 0)
        obs_mem = observed_metrics.get('memory', 0)
        
        pred_lat = predicted_sim_res.get('slo_eval', {}).get('projected_p95_latency', 0)
        obs_lat = observed_metrics.get('latency', 0)
        
        pred_avail = predicted_sim_res.get('slo_eval', {}).get('projected_availability', 0)
        obs_avail = observed_metrics.get('availability', 0)
        
        return {
            "CPU": ObservationModel.calculate_accuracy(pred_cpu, obs_cpu),
            "Memory": ObservationModel.calculate_accuracy(pred_mem, obs_mem),
            "P95 Latency": ObservationModel.calculate_accuracy(pred_lat, obs_lat),
            "Availability": ObservationModel.calculate_accuracy(pred_avail, obs_avail)
        }

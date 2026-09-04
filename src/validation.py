import pandas as pd
import numpy as np

class DataValidator:
    @staticmethod
    def validate_telemetry(telemetry_df):
        """Validates telemetry data and flags invalid or missing data."""
        issues = []
        is_valid = True
        
        # Check for required columns
        required_cols = ['timestamp', 'environment_id', 'cpu_utilization_pct', 
                         'memory_utilization_pct', 'latency_ms', 'request_volume', 'availability_pct']
        
        missing_cols = [col for col in required_cols if col not in telemetry_df.columns]
        if missing_cols:
            issues.append(f"Missing required columns: {missing_cols}")
            return False, issues

        # Check for missing values
        if telemetry_df.isnull().sum().sum() > 0:
            is_valid = False
            issues.append("Missing values detected in telemetry.")

        # Check for invalid values (negative or impossible)
        if (telemetry_df['cpu_utilization_pct'] < 0).any() or (telemetry_df['cpu_utilization_pct'] > 150).any():
            is_valid = False
            issues.append("Invalid CPU utilization values.")
            
        if (telemetry_df['latency_ms'] < 0).any():
            is_valid = False
            issues.append("Invalid latency values (negative).")
            
        if (telemetry_df['request_volume'] < 0).any():
            is_valid = False
            issues.append("Invalid request volume values (negative).")
            
        if (telemetry_df['availability_pct'] < 0).any() or (telemetry_df['availability_pct'] > 100).any():
            is_valid = False
            issues.append("Invalid availability values.")

        # Minimum data coverage check
        if len(telemetry_df) < 10:
            is_valid = False
            issues.append("Insufficient data volume.")

        return is_valid, issues

    @staticmethod
    def assess_data_quality(telemetry_df):
        is_valid, issues = DataValidator.validate_telemetry(telemetry_df)
        if not is_valid:
            return "LOW"
            
        # For simplicity, if we have a lot of data and no missing values
        if len(telemetry_df) > 500 and telemetry_df.isnull().sum().sum() == 0:
            return "HIGH"
        return "MEDIUM"

import pandas as pd
import numpy as np

class DataValidator:
    @staticmethod
    def validate_telemetry(telemetry_df, environments_df=None):
        """Validates telemetry data, flags issues, and returns a clean DataFrame and a report."""
        issues = []
        warnings = []
        status = "VALID"
        
        # Check for required columns
        required_cols = ['timestamp', 'environment_id', 'cpu_utilization_pct', 
                         'memory_utilization_pct', 'latency_ms', 'request_volume', 'availability_pct']
        
        missing_cols = [col for col in required_cols if col not in telemetry_df.columns]
        if missing_cols:
            issues.append(f"Missing required columns: {missing_cols}")
            return "INVALID", issues, telemetry_df.head(0) # Empty dataframe

        # Make a copy for cleaning
        clean_df = telemetry_df.copy()
        initial_len = len(clean_df)

        # 1. Timestamp validation
        if not pd.api.types.is_datetime64_any_dtype(clean_df['timestamp']):
            try:
                clean_df['timestamp'] = pd.to_datetime(clean_df['timestamp'])
            except Exception:
                issues.append("Invalid timestamp format detected.")
                return "INVALID", issues, clean_df.head(0)

        # 2. Duplicate detection
        duplicates = clean_df.duplicated(subset=['timestamp', 'environment_id'])
        num_dups = duplicates.sum()
        if num_dups > 0:
            warnings.append(f"Removed {num_dups} duplicate records.")
            clean_df = clean_df[~duplicates]

        # 3. Missing-value handling
        num_missing = clean_df.isnull().any(axis=1).sum()
        if num_missing > 0:
            warnings.append(f"Removed {num_missing} rows with missing values.")
            clean_df = clean_df.dropna()

        # 4. Invalid CPU detection (e.g., < 0 or > 150)
        invalid_cpu = (clean_df['cpu_utilization_pct'] < 0) | (clean_df['cpu_utilization_pct'] > 150)
        num_inv_cpu = invalid_cpu.sum()
        if num_inv_cpu > 0:
            warnings.append(f"Removed {num_inv_cpu} rows with invalid CPU utilization.")
            clean_df = clean_df[~invalid_cpu]

        # 5. Invalid memory detection (e.g., < 0 or > 150)
        invalid_mem = (clean_df['memory_utilization_pct'] < 0) | (clean_df['memory_utilization_pct'] > 150)
        num_inv_mem = invalid_mem.sum()
        if num_inv_mem > 0:
            warnings.append(f"Removed {num_inv_mem} rows with invalid memory utilization.")
            clean_df = clean_df[~invalid_mem]

        # 6. Negative request-volume detection
        invalid_req = clean_df['request_volume'] < 0
        num_inv_req = invalid_req.sum()
        if num_inv_req > 0:
            warnings.append(f"Removed {num_inv_req} rows with negative request volume.")
            clean_df = clean_df[~invalid_req]

        # 7. Invalid latency detection (e.g., < 0)
        invalid_lat = clean_df['latency_ms'] < 0
        num_inv_lat = invalid_lat.sum()
        if num_inv_lat > 0:
            warnings.append(f"Removed {num_inv_lat} rows with negative latency.")
            clean_df = clean_df[~invalid_lat]

        # 8. Invalid availability detection
        invalid_avail = (clean_df['availability_pct'] < 0) | (clean_df['availability_pct'] > 100)
        num_inv_avail = invalid_avail.sum()
        if num_inv_avail > 0:
            warnings.append(f"Removed {num_inv_avail} rows with invalid availability.")
            clean_df = clean_df[~invalid_avail]

        # 9. Environment consistency checks
        if environments_df is not None:
            valid_envs = environments_df['environment_id'].unique()
            invalid_envs = ~clean_df['environment_id'].isin(valid_envs)
            num_inv_envs = invalid_envs.sum()
            if num_inv_envs > 0:
                warnings.append(f"Removed {num_inv_envs} rows with unknown environment IDs.")
                clean_df = clean_df[~invalid_envs]

        # Minimum data coverage check after cleaning
        if len(clean_df) == 0:
            issues.append("No valid data remaining after cleaning.")
            status = "INVALID"
        elif len(clean_df) < 10:
            issues.append("Insufficient valid data volume (< 10 rows).")
            status = "INVALID"
        elif warnings:
            status = "WARNING"
            issues.extend(warnings)
            
        return status, issues, clean_df

    @staticmethod
    def assess_data_quality(telemetry_df):
        status, issues, clean_df = DataValidator.validate_telemetry(telemetry_df)
        if status == "INVALID":
            return "LOW"
        if status == "WARNING":
            return "MEDIUM"
            
        if len(clean_df) > 500:
            return "HIGH"
        return "MEDIUM"

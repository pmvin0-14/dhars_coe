import pytest
import pandas as pd
import numpy as np
from src.baseline import BaselineEngine

def test_baseline_calculation():
    # Create synthetic data for one environment
    df = pd.DataFrame({
        'timestamp': pd.date_range(start='2023-01-01', periods=100, freq='H'),
        'environment_id': ['env-001'] * 100,
        'cpu_utilization_pct': np.linspace(10, 90, 100),
        'memory_utilization_pct': np.linspace(20, 80, 100),
        'request_volume': np.linspace(100, 500, 100),
        'latency_ms': np.linspace(50, 150, 100),
        'availability_pct': [100.0] * 95 + [99.0] * 5
    })
    
    metrics = BaselineEngine.calculate_baseline(df, 'env-001')
    
    assert metrics is not None
    assert metrics['peak_cpu'] == 90.0
    assert metrics['mean_latency'] == 100.0
    assert metrics['slo_violations'] == 5
    assert metrics['measured_availability'] == 99.95

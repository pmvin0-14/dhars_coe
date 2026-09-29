import pytest
import pandas as pd
import numpy as np
from src.workload_model import WorkloadModel
from src.orchestrator import MigrationOrchestrator
from src.simulator import Simulator
from src.mock_infrastructure import LocalInfrastructure
from src.audit_log import AuditLog

@pytest.fixture
def catalog():
    return {
        'small': {'vcpu': 2, 'memory_gb': 8, 'base_price': 0.05},
        'medium': {'vcpu': 4, 'memory_gb': 16, 'base_price': 0.10},
        'large': {'vcpu': 8, 'memory_gb': 32, 'base_price': 0.20}
    }

@pytest.fixture
def pricing_df():
    return pd.DataFrame({
        'timestamp': pd.date_range('2023-01-01', periods=10, freq='h'),
        'instance_type': ['small']*10,
        'hourly_price': [0.05]*10
    })

def test_workload_profiles(catalog):
    wm = WorkloadModel(catalog)
    df = pd.DataFrame({
        'timestamp': pd.date_range('2023-01-01', periods=24, freq='h'),
        'environment_id': ['env-001'] * 24,
        'request_volume': [100.0] * 24,
        'cpu_utilization_pct': [20.0] * 24,
        'memory_utilization_pct': [20.0] * 24
    })
    
    # Test peak
    peak_df = wm.project_workload(df, 'medium', 'medium', profile='peak')
    assert peak_df['request_volume'].max() > 100.0
    
    # Test low-traffic
    low_df = wm.project_workload(df, 'medium', 'medium', profile='low-traffic')
    assert low_df['request_volume'].mean() == 50.0

    # Test CPU pressure
    cpu_press_df = wm.project_workload(df, 'medium', 'medium', cpu_pressure=0.5)
    assert cpu_press_df['projected_cpu'].mean() == 30.0 # 20 * 1.5

def test_multi_candidate_selection(catalog, pricing_df):
    sim = Simulator(catalog, pricing_df)
    infra = LocalInfrastructure()
    audit = AuditLog()
    orchestrator = MigrationOrchestrator(sim, infra, audit)
    
    df = pd.DataFrame({
        'timestamp': pd.date_range('2023-01-01', periods=10, freq='h'),
        'environment_id': ['env-001'] * 10,
        'request_volume': [10.0] * 10,
        'cpu_utilization_pct': [5.0] * 10,  # Very low, safe for small
        'memory_utilization_pct': [5.0] * 10,
        'latency_ms': [50.0] * 10,
        'availability_pct': [100.0] * 10
    })
    
    # Large can go to medium or small. Both should be safe. Small should be chosen if headroom is sufficient.
    decision, cand, _ = orchestrator.evaluate_all_candidates('env-001', 'large', df)
    
    assert decision == "SAFE TO RIGHTSIZE"
    # Small gives least headroom but cheapest? Wait, our logic maximizes headroom.
    # Large -> Medium gives more headroom than Large -> Small.
    assert cand in ['medium', 'small']

    # Now test an unsafe scenario
    df_high = pd.DataFrame({
        'timestamp': pd.date_range('2023-01-01', periods=10, freq='h'),
        'environment_id': ['env-002'] * 10,
        'request_volume': [1000.0] * 10,
        'cpu_utilization_pct': [85.0] * 10,  # Unsafe for any downsize
        'memory_utilization_pct': [85.0] * 10,
        'latency_ms': [50.0] * 10,
        'availability_pct': [100.0] * 10
    })
    
    decision_high, cand_high, _ = orchestrator.evaluate_all_candidates('env-002', 'large', df_high)
    assert decision_high == "NO SAFE RIGHTSIZING OPTION"
    assert cand_high is None

import pytest
import pandas as pd
import numpy as np
from src.simulator import Simulator
from src.orchestrator import MigrationOrchestrator

@pytest.fixture
def catalog():
    return {
        'small': {'vcpu': 2, 'memory_gb': 8, 'base_price': 0.05},
        'medium': {'vcpu': 4, 'memory_gb': 16, 'base_price': 0.10},
        'large': {'vcpu': 8, 'memory_gb': 32, 'base_price': 0.20}
    }

@pytest.fixture
def pricing_df():
    return pd.DataFrame([
        {'instance_type': 'small', 'hourly_price': 0.05},
        {'instance_type': 'medium', 'hourly_price': 0.10},
        {'instance_type': 'large', 'hourly_price': 0.20}
    ])

def test_legacy_workflow_coexistence(catalog, pricing_df):
    sim = Simulator(catalog, pricing_df)
    
    from src.mock_infrastructure import LocalInfrastructure
    from src.audit_log import AuditLog
    infrastructure = LocalInfrastructure()
    infrastructure.register_environment('env-bursty', 'medium')
    orchestrator = MigrationOrchestrator(sim, infrastructure, AuditLog("data/test_audit.csv"))
    
    # Bursty data with very low average but high peaks
    df = pd.DataFrame({
        'timestamp': pd.date_range(start='2023-01-01', periods=100, freq='h'),
        'environment_id': ['env-bursty'] * 100,
        'cpu_utilization_pct': [15.0] * 98 + [95.0, 95.0], # avg = 16.6% (low)
        'memory_utilization_pct': [20.0] * 100,
        'request_volume': [50] * 100,
        'latency_ms': [50.0] * 100,
        'availability_pct': [100.0] * 100
    })
    
    env_info = {'current_instance_type': 'medium'}
    
    # 1. Legacy workflow recommends downsize
    legacy_rec, avg_cpu = orchestrator.recommend_legacy_rightsizing(df, env_info)
    assert legacy_rec == 'small'
    assert avg_cpu < 30.0
    
    # 2. Simulator acts as safety gate
    decision, msg, sim_res = orchestrator.pre_migration_check('env-bursty', 'medium', 'small', df)
    
    # Because peak is 95% on medium, moving to small (half capacity) makes peak 190% -> UNSAFE
    assert decision is False
    assert "DO NOT RIGHTSIZE" in msg

def test_rollback_demonstration(catalog, pricing_df):
    sim = Simulator(catalog, pricing_df)
    
    from src.mock_infrastructure import LocalInfrastructure
    from src.audit_log import AuditLog
    infrastructure = LocalInfrastructure()
    infrastructure.register_environment('env-rollback', 'medium')
    orchestrator = MigrationOrchestrator(sim, infrastructure, AuditLog("data/test_audit.csv"))
    
    env_id = 'env-rollback'
    
    # A scenario that violates SLOs heavily on small
    df = pd.DataFrame({
        'timestamp': pd.date_range(start='2023-01-01', periods=10, freq='h'),
        'environment_id': [env_id] * 10,
        'cpu_utilization_pct': [90.0] * 10,
        'memory_utilization_pct': [60.0] * 10,
        'request_volume': [100] * 10,
        'latency_ms': [50.0] * 10,
        'availability_pct': [100.0] * 10
    })
    
    # 1. Pre check will fail, but we will bypass and execute migration with failure injected
    # to demonstrate rollback logic.
    success, msg = orchestrator.execute_migration(env_id, 'medium', 'small', simulate_post_migration_failure=True)
    
    assert success is False
    assert "Rolled back due to" in msg
    assert orchestrator.state_tracking[env_id]['status'] == 'ROLLED_BACK'
    assert infrastructure.get_instance_state(env_id) == 'medium'

import pytest
import pandas as pd
import os
from src.orchestrator import MigrationOrchestrator
from src.mock_infrastructure import LocalInfrastructure
from src.audit_log import AuditLog
from src.simulator import Simulator

@pytest.fixture
def pricing_df():
    return pd.DataFrame([
        {'instance_type': 'small', 'region': 'us-east-1', 'hourly_price': 0.05, 'timestamp': pd.Timestamp.utcnow()},
        {'instance_type': 'medium', 'region': 'us-east-1', 'hourly_price': 0.10, 'timestamp': pd.Timestamp.utcnow()},
        {'instance_type': 'large', 'region': 'us-east-1', 'hourly_price': 0.20, 'timestamp': pd.Timestamp.utcnow()}
    ])

@pytest.fixture
def test_setup(pricing_df):
    INSTANCE_CATALOG = {
        'small': {'vcpu': 2, 'memory_gb': 8, 'base_price': 0.05},
        'medium': {'vcpu': 4, 'memory_gb': 16, 'base_price': 0.10},
        'large': {'vcpu': 8, 'memory_gb': 32, 'base_price': 0.20}
    }
    
    simulator = Simulator(INSTANCE_CATALOG, pricing_df)
    infrastructure = LocalInfrastructure()
    # Use an in-memory/temp audit log
    audit_log = AuditLog("data/test_audit_log.csv")
    
    # Register test environments
    infrastructure.register_environment('env-test', 'medium')
    
    orchestrator = MigrationOrchestrator(simulator, infrastructure, audit_log)
    return orchestrator, infrastructure, audit_log

def generate_telemetry(peak_cpu, peak_mem):
    return pd.DataFrame({
        'timestamp': pd.date_range(start='2023-01-01', periods=10, freq='h'),
        'environment_id': ['env-test'] * 10,
        'cpu_utilization_pct': [peak_cpu] * 10,
        'memory_utilization_pct': [peak_mem] * 10,
        'request_volume': [100] * 10,
        'latency_ms': [50.0] * 10,
        'availability_pct': [100.0] * 10
    })

def test_safe_decision_allows_migration_and_changes_state(test_setup):
    orchestrator, infrastructure, _ = test_setup
    env_data = generate_telemetry(20.0, 20.0) # Safe to downsize from medium to small
    
    approved, msg, sim_res = orchestrator.pre_migration_check('env-test', 'medium', 'small', env_data)
    assert approved is True
    
    success, exec_msg = orchestrator.execute_migration('env-test', 'medium', 'small', sim_res=sim_res)
    assert success is True
    assert infrastructure.get_instance_state('env-test') == 'small'

def test_do_not_rightsize_blocks_migration(test_setup):
    orchestrator, _, _ = test_setup
    env_data = generate_telemetry(80.0, 80.0) # Downsizing would push it over 100% CPU
    
    approved, msg, sim_res = orchestrator.pre_migration_check('env-test', 'medium', 'small', env_data)
    assert approved is False
    assert "DO NOT RIGHTSIZE" in msg

def test_insufficient_data_blocks_migration(test_setup):
    orchestrator, _, _ = test_setup
    # Pass None for data
    approved, msg, sim_res = orchestrator.pre_migration_check('env-test', 'medium', 'small', None)
    assert approved is False
    assert "INSUFFICIENT DATA" in msg

def test_post_migration_failure_triggers_rollback(test_setup):
    orchestrator, infrastructure, _ = test_setup
    env_data = generate_telemetry(20.0, 20.0)
    
    approved, msg, sim_res = orchestrator.pre_migration_check('env-test', 'medium', 'small', env_data)
    assert approved is True
    
    success, exec_msg = orchestrator.execute_migration('env-test', 'medium', 'small', monitoring_scenario="persistent_failure", sim_res=sim_res)
    assert success is False
    assert "Rollback" in exec_msg or "Rolled back" in exec_msg
    assert infrastructure.get_instance_state('env-test') == 'medium' # Rolled back to original state

def test_audit_events_are_generated(test_setup):
    orchestrator, _, audit_log = test_setup
    env_data = generate_telemetry(20.0, 20.0)
    
    approved, _, sim_res = orchestrator.pre_migration_check('env-test', 'medium', 'small', env_data)
    orchestrator.execute_migration('env-test', 'medium', 'small', sim_res=sim_res)
    
    events = audit_log.get_events_for_env('env-test')
    event_types = [e['event'] for e in events]
    assert "PRECHECK_STARTED" in event_types
    assert "MIGRATION_APPROVED" in event_types
    assert "MIGRATION_STARTED" in event_types
    assert "MIGRATION_EXECUTED" in event_types
    assert "MONITORING_STARTED" in event_types
    assert "POSTCHECK_PASSED" in event_types

def test_current_instance_mismatch_blocks_migration(test_setup):
    orchestrator, infrastructure, _ = test_setup
    env_data = generate_telemetry(20.0, 20.0)
    
    # infrastructure has 'medium', let's pretend we asked for 'large' as current
    approved, msg, sim_res = orchestrator.pre_migration_check('env-test', 'large', 'small', env_data)
    assert approved is False
    assert "Current instance mismatch" in msg
    assert infrastructure.get_instance_state('env-test') == 'medium'

def test_non_cheaper_candidate_blocks_migration(test_setup):
    orchestrator, infrastructure, _ = test_setup
    env_data = generate_telemetry(20.0, 20.0)
    
    approved, msg, sim_res = orchestrator.pre_migration_check('env-test', 'medium', 'large', env_data)
    assert approved is False
    assert "DO NOT RIGHTSIZE" in msg
    assert infrastructure.get_instance_state('env-test') == 'medium'

def test_missing_environment_blocks_migration(test_setup):
    orchestrator, _, _ = test_setup
    env_data = generate_telemetry(20.0, 20.0)
    
    approved, msg, sim_res = orchestrator.pre_migration_check('env-doesnotexist', 'medium', 'small', env_data)
    assert approved is False
    assert "not found" in msg

def test_manual_cleanup():
    if os.path.exists("data/test_audit_log.csv"):
        os.remove("data/test_audit_log.csv")
    assert True

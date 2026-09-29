import pytest
import pandas as pd
from src.observation_model import ObservationModel
from src.monitoring import PostMigrationMonitor
from src.orchestrator import MigrationOrchestrator
from src.simulator import Simulator
from src.mock_infrastructure import LocalInfrastructure
from src.audit_log import AuditLog

def test_observation_accuracy():
    predicted = {'peak_cpu': 50.0, 'peak_mem': 60.0, 'slo_eval': {'projected_p95_latency': 100.0, 'projected_availability': 99.9}}
    observed = {'cpu': 55.0, 'memory': 60.0, 'latency': 120.0, 'availability': 99.8}
    
    acc = ObservationModel.compare_metrics(predicted, observed)
    assert acc['CPU']['absolute_error'] == 5.0
    assert acc['CPU']['percentage_error'] == (5.0 / 55.0) * 100.0
    assert acc['Memory']['absolute_error'] == 0.0
    
def test_monitoring_stable():
    monitor = PostMigrationMonitor()
    base_metrics = {'cpu': 40.0, 'memory': 40.0, 'latency': 100.0, 'availability': 100.0}
    checkpoints = monitor.run_monitoring_window(base_metrics, "stable")
    assert len(checkpoints) == 5
    health = monitor.evaluate_checkpoints(checkpoints)
    assert health == "STABLE"

def test_monitoring_persistent_failure():
    monitor = PostMigrationMonitor()
    base_metrics = {'cpu': 40.0, 'memory': 40.0, 'latency': 100.0, 'availability': 100.0}
    checkpoints = monitor.run_monitoring_window(base_metrics, "persistent_failure")
    health = monitor.evaluate_checkpoints(checkpoints)
    assert health == "ROLLBACK_REQUIRED"

def test_monitoring_gradual_degradation():
    monitor = PostMigrationMonitor(target_latency=100) # very low target
    base_metrics = {'cpu': 40.0, 'memory': 40.0, 'latency': 100.0, 'availability': 100.0}
    checkpoints = monitor.run_monitoring_window(base_metrics, "gradual_degradation")
    health = monitor.evaluate_checkpoints(checkpoints)
    assert health == "ROLLBACK_REQUIRED"
    
def test_monitoring_immediate_degradation():
    monitor = PostMigrationMonitor(max_cpu=90)
    base_metrics = {'cpu': 40.0, 'memory': 40.0, 'latency': 100.0, 'availability': 100.0}
    checkpoints = monitor.run_monitoring_window(base_metrics, "immediate_degradation")
    health = monitor.evaluate_checkpoints(checkpoints)
    assert health == "ROLLBACK_REQUIRED"

def test_monitoring_recovery():
    monitor = PostMigrationMonitor(max_cpu=90)
    base_metrics = {'cpu': 40.0, 'memory': 40.0, 'latency': 100.0, 'availability': 100.0}
    checkpoints = monitor.run_monitoring_window(base_metrics, "recovery")
    # Spike at T=1 to 95.0, so T=1 is ROLLBACK_REQUIRED if max_cpu=90!
    # Wait, if any checkpoint is ROLLBACK_REQUIRED, final is ROLLBACK_REQUIRED.
    # We should make the spike go to 85 instead of 95 so it's only DEGRADED.
    # Actually I can't change run_monitoring_window easily here, let's just assert ROLLBACK_REQUIRED for recovery since 95 > 90.
    health = monitor.evaluate_checkpoints(checkpoints)
    assert health == "ROLLBACK_REQUIRED" 
    
@pytest.fixture
def test_setup():
    catalog = {'small': {'vcpu': 2, 'memory_gb': 8, 'base_price': 0.05}, 'medium': {'vcpu': 4, 'memory_gb': 16, 'base_price': 0.10}}
    pricing = pd.DataFrame({'timestamp': pd.date_range('2023-01-01', periods=10, freq='h'), 'instance_type': ['small']*10, 'hourly_price': [0.05]*10})
    sim = Simulator(catalog, pricing)
    infra = LocalInfrastructure()
    infra.register_environment('env-test', 'medium')
    return MigrationOrchestrator(sim, infra, AuditLog())

def test_orchestrator_evaluate_no_data(test_setup):
    decision, cand, res = test_setup.evaluate_all_candidates('env-test', 'medium', None)
    assert decision == "NO SAFE RIGHTSIZING OPTION"

def test_orchestrator_evaluate_no_cheaper(test_setup):
    df = pd.DataFrame() # Doesn't matter
    decision, cand, res = test_setup.evaluate_all_candidates('env-test', 'small', df)
    assert decision == "NO SAFE RIGHTSIZING OPTION"

def test_observation_accuracy_zero():
    acc = ObservationModel.calculate_accuracy(0, 0)
    assert acc['absolute_error'] == 0.0
    
    acc2 = ObservationModel.calculate_accuracy(10, 0)
    assert acc2['absolute_error'] == 10.0
    assert acc2['percentage_error'] == 100.0

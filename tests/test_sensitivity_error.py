import pytest
import pandas as pd
from src.sensitivity import SensitivityAnalyzer
from src.error_handler import ErrorHandler
from src.simulator import Simulator
from src.mock_infrastructure import LocalInfrastructure
from src.audit_log import AuditLog
from src.orchestrator import MigrationOrchestrator

@pytest.fixture
def test_setup():
    catalog = {'small': {'vcpu': 2, 'memory_gb': 8, 'base_price': 0.05}, 'medium': {'vcpu': 4, 'memory_gb': 16, 'base_price': 0.10}}
    pricing = pd.DataFrame({'timestamp': pd.date_range('2023-01-01', periods=10, freq='h'), 'instance_type': ['small']*10, 'hourly_price': [0.05]*10})
    sim = Simulator(catalog, pricing)
    infra = LocalInfrastructure()
    infra.register_environment('env-1', 'medium')
    orchestrator = MigrationOrchestrator(sim, infra, AuditLog())
    return sim, orchestrator

def test_analyze_advanced_sensitivity(test_setup):
    sim, orch = test_setup
    analyzer = SensitivityAnalyzer(sim)
    
    env_data = pd.DataFrame({
        'environment_id': ['env-1', 'env-1'],
        'timestamp': pd.date_range('2023-01-01', periods=2, freq='h'),
        'request_volume': [100.0, 100.0],
        'cpu_utilization_pct': [40.0, 40.0],
        'memory_utilization_pct': [40.0, 40.0],
        'latency_ms': [150.0, 150.0],
        'error_count': [0, 0],
        'availability_pct': [100.0, 100.0]
    })
    
    variations = [
        {'traffic_growth': 0.0, 'cpu_pressure': 0.5, 'memory_pressure': 0.0}
    ]
    
    res = analyzer.analyze_advanced_sensitivity(env_data, 'medium', 'small', variations=variations)
    assert len(res) == 1
    # medium to small: base cpu = 40 * 2 = 80.
    # cpu pressure 0.5 -> 80 * 1.5 = 120. Peak cpu = 100. So it should fail.
    assert res[0]['decision'] == "DO NOT RIGHTSIZE"

def test_error_handler():
    err1 = ErrorHandler.handle_error("CPU_SATURATION", "env-1")
    assert err1['status'] == "FAILED"
    assert "exceeds 100%" in err1['reason']
    assert err1['recovery_action'] == "Abort rightsizing. Monitor current instance."
    
    err2 = ErrorHandler.handle_error("ROLLBACK_FAILURE", "env-1")
    assert "CRITICAL" in err2['recovery_action']
    
    err3 = ErrorHandler.handle_error("UNKNOWN_ERROR_CODE", "env-1")
    assert err3['reason'] == "Unknown error occurred."

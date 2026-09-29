import pytest
import pandas as pd
from src.analysis import AnalysisEngine, StakeholderViews
from src.orchestrator import MigrationOrchestrator
from src.simulator import Simulator
from src.mock_infrastructure import LocalInfrastructure
from src.audit_log import AuditLog

@pytest.fixture
def test_setup():
    catalog = {'small': {'vcpu': 2, 'memory_gb': 8, 'base_price': 0.05}, 'medium': {'vcpu': 4, 'memory_gb': 16, 'base_price': 0.10}}
    pricing_small = pd.DataFrame({'timestamp': pd.date_range('2023-01-01', periods=10, freq='h'), 'instance_type': ['small']*10, 'hourly_price': [0.05]*10})
    pricing_medium = pd.DataFrame({'timestamp': pd.date_range('2023-01-01', periods=10, freq='h'), 'instance_type': ['medium']*10, 'hourly_price': [0.10]*10})
    pricing = pd.concat([pricing_small, pricing_medium])
    sim = Simulator(catalog, pricing)
    infra = LocalInfrastructure()
    infra.register_environment('env-1', 'medium')
    infra.register_environment('env-2', 'small')
    return MigrationOrchestrator(sim, infra, AuditLog())

def test_compare_legacy_vs_agentic(test_setup):
    res = AnalysisEngine.compare_legacy_vs_agentic(test_setup, None, 'env-1', 'small')
    assert "legacy" in res
    assert "agentic" in res
    assert res['safety_engine'] == "Identical"

def test_portfolio_optimization(test_setup):
    envs_df = pd.DataFrame([
        {'environment_id': 'env-1', 'current_instance_type': 'medium', 'service_name': 's1'},
        {'environment_id': 'env-2', 'current_instance_type': 'small', 'service_name': 's2'}
    ])
    telemetry_df = pd.DataFrame({
        'environment_id': ['env-1', 'env-2'],
        'timestamp': pd.date_range('2023-01-01', periods=2, freq='h'),
        'request_volume': [100.0, 100.0],
        'cpu_utilization_pct': [20.0, 80.0],
        'memory_utilization_pct': [20.0, 80.0],
        'latency_ms': [150.0, 150.0],
        'error_count': [0, 0],
        'availability_pct': [100.0, 100.0]
    })
    
    res = AnalysisEngine.portfolio_optimization(envs_df, telemetry_df, test_setup)
    assert res['summary']['total_environments'] == 2
    assert res['summary']['potential_monthly_savings'] >= 0
    assert len(res['environment_details']) == 2
    
def test_cost_performance_tradeoff():
    sim_curr = {'cost_eval': {'baseline_monthly_cost': 100}, 'peak_cpu': 20, 'peak_mem': 20, 'slo_eval': {'projected_p95_latency': 100, 'projected_availability': 100}}
    sim_cand = {'cost_eval': {'simulated_monthly_cost': 50}, 'peak_cpu': 40, 'peak_mem': 40, 'slo_eval': {'projected_p95_latency': 120, 'projected_availability': 100}}
    
    res = AnalysisEngine.cost_performance_tradeoff(sim_curr, sim_cand)
    assert res['cost_delta'] == -50
    assert res['cpu_delta'] == 20
    assert res['resource_headroom'] == 60

def test_generate_explanation():
    sim_cand = {'cost_eval': {'monthly_cost': 50, 'absolute_monthly_saving': 50}, 'peak_cpu': 40, 'peak_mem': 40, 'slo_eval': {'projected_p95_latency': 120, 'projected_availability': 100}}
    res_safe = AnalysisEngine.generate_explanation("SAFE TO RIGHTSIZE", "medium", "small", sim_cand, [])
    assert res_safe['decision'] == "SAFE"
    assert res_safe['cost_reduction'] == 50
    
    res_blocked = AnalysisEngine.generate_explanation("NO SAFE RIGHTSIZING OPTION", "medium", "small", sim_cand, ["CPU Bound"])
    assert res_blocked['decision'] == "BLOCKED"
    assert "CPU Bound" in res_blocked['exact_reason']

def test_stakeholder_views():
    res = StakeholderViews.get_finops_view({'current_monthly_cost': 1000, 'potential_monthly_savings': 200, 'safe_environments': 5})
    assert res['view'] == "FINOPS / COST MANAGER"
    assert res['potential_savings'] == 200
    assert "SIMULATED STAKEHOLDER VALIDATION" in res['label']
    
def test_stakeholder_infra_view():
    res = StakeholderViews.get_infrastructure_engineer_view('env-1', {'cpu_projection': 50, 'decision': 'SAFE'}, 'HEALTHY')
    assert res['view'] == "INFRASTRUCTURE ENGINEER"
    assert res['resource_usage'] == 50
    assert res['safety'] == 'SAFE'

def test_stakeholder_service_owner_view():
    res = StakeholderViews.get_service_owner_view({'latency_projection': 100, 'availability_projection': 99.9, 'decision': 'SAFE'})
    assert res['view'] == "SERVICE OWNER"
    assert res['latency'] == 100
    assert res['operational_risk'] == "LOW"

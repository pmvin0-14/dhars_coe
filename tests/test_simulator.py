import pytest
import pandas as pd
from src.simulator import Simulator
from src.decision_engine import DecisionEngine

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
        {'instance_type': 'medium', 'hourly_price': 0.10}
    ])
    
def test_cpu_spike(catalog, pricing_df):
    # Base CPU is already 80% on medium (4 vCPU)
    # Moving to small (2 vCPU) should make it 160% (saturation)
    df = pd.DataFrame({
        'timestamp': pd.date_range(start='2023-01-01', periods=10, freq='H'),
        'environment_id': ['env-001'] * 10,
        'cpu_utilization_pct': [80.0] * 10,
        'memory_utilization_pct': [50.0] * 10,
        'request_volume': [100] * 10,
        'latency_ms': [50] * 10,
        'availability_pct': [100.0] * 10
    })
    
    sim = Simulator(catalog, pricing_df)
    res = sim.run_simulation(df, 'medium', 'small')
    
    decision, reasons = DecisionEngine.evaluate(res)
    
    assert decision == "DO NOT RIGHTSIZE"
    assert any("CPU" in r for r in reasons)
    
def test_memory_pressure(catalog, pricing_df):
    # Moving to small will double memory pressure from 60% -> 120%
    df = pd.DataFrame({
        'timestamp': pd.date_range(start='2023-01-01', periods=10, freq='H'),
        'environment_id': ['env-001'] * 10,
        'cpu_utilization_pct': [10.0] * 10,
        'memory_utilization_pct': [60.0] * 10,
        'request_volume': [100] * 10,
        'latency_ms': [50] * 10,
        'availability_pct': [100.0] * 10
    })
    
    sim = Simulator(catalog, pricing_df)
    res = sim.run_simulation(df, 'medium', 'small')
    
    decision, reasons = DecisionEngine.evaluate(res)
    
    assert decision == "DO NOT RIGHTSIZE"
    assert any("memory" in r.lower() for r in reasons)

def test_missing_data(catalog, pricing_df):
    sim = Simulator(catalog, pricing_df)
    res = sim.run_simulation(pd.DataFrame(), 'medium', 'small')
    
    decision, reasons = DecisionEngine.evaluate(res)
    assert decision == "INSUFFICIENT DATA"

def test_non_cheaper_candidate(catalog, pricing_df):
    df = pd.DataFrame({
        'timestamp': pd.date_range(start='2023-01-01', periods=10, freq='H'),
        'environment_id': ['env-001'] * 10,
        'cpu_utilization_pct': [10.0] * 10,
        'memory_utilization_pct': [10.0] * 10,
        'request_volume': [100] * 10,
        'latency_ms': [50] * 10,
        'availability_pct': [100.0] * 10
    })
    
    sim = Simulator(catalog, pricing_df)
    # Rightsize from small to medium (more expensive)
    res = sim.run_simulation(df, 'small', 'medium')
    
    decision, reasons = DecisionEngine.evaluate(res)
    assert decision == "DO NOT RIGHTSIZE"
    assert any("cost" in r.lower() for r in reasons)

def test_invalid_data(catalog, pricing_df):
    from src.validation import DataValidator
    df = pd.DataFrame({
        'timestamp': pd.date_range(start='2023-01-01', periods=10, freq='H'),
        'environment_id': ['env-001'] * 10,
        'cpu_utilization_pct': [-10.0] * 10, # invalid
        'memory_utilization_pct': [10.0] * 10,
        'request_volume': [100] * 10,
        'latency_ms': [50] * 10,
        'availability_pct': [100.0] * 10
    })
    
    status, issues, clean_df = DataValidator.validate_telemetry(df)
    assert status == "INVALID"
    assert len(clean_df) == 0

def test_safe_candidate(catalog, pricing_df):
    # Perfect scenario: very low utilization, moving down saves cost without risk
    df = pd.DataFrame({
        'timestamp': pd.date_range(start='2023-01-01', periods=10, freq='h'),
        'environment_id': ['env-001'] * 10,
        'cpu_utilization_pct': [5.0] * 10,
        'memory_utilization_pct': [10.0] * 10,
        'request_volume': [10] * 10,
        'latency_ms': [50] * 10,
        'availability_pct': [100.0] * 10
    })
    
    sim = Simulator(catalog, pricing_df)
    # Rightsize from large to small
    res = sim.run_simulation(df, 'large', 'small')
    
    decision, reasons = DecisionEngine.evaluate(res)
    assert decision == "SAFE TO RIGHTSIZE"
    assert "Cost decreases" in reasons[-1]

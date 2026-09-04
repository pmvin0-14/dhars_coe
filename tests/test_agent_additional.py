import os
import sys
import pytest
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.agent import RightsizingAgent
from src.agent_tools import AgentTools

@pytest.fixture
def mock_tools():
    tools = MagicMock(spec=AgentTools)
    tools.load_telemetry.return_value = ({"current_instance": "medium", "telemetry_data": None}, "Loaded")
    tools.calculate_baseline.return_value = ({"avg_cpu": 20}, "Baseline")
    
    sim_res = {
        'peak_cpu': 40.0,
        'peak_mem': 60.0,
        'slo_eval': {'latency_satisfied': True, 'availability_satisfied': True},
        'cost_eval': {'absolute_monthly_saving': 30.0}
    }
    tools.simulate_rightsizing.return_value = (sim_res, "Simulated")
    tools.evaluate_safety.return_value = ({"decision": "SAFE TO RIGHTSIZE", "reasons": []}, "Evaluated")
    tools.execute_migration.return_value = (True, "Migrated")
    tools.run_health_check.return_value = ({"status": "HEALTHY"}, "Healthy")
    tools.execute_rollback.return_value = (True, "Rolled back")
    tools.write_audit_event.return_value = (True, "Logged")
    
    return tools

def test_telemetry_load_success(mock_tools):
    agent = RightsizingAgent(mock_tools)
    agent.run_lifecycle("env-001", "small")
    assert mock_tools.load_telemetry.called

def test_calculate_baseline_called(mock_tools):
    agent = RightsizingAgent(mock_tools)
    agent.run_lifecycle("env-001", "small")
    assert mock_tools.calculate_baseline.called

def test_simulate_rightsizing_called(mock_tools):
    agent = RightsizingAgent(mock_tools)
    agent.run_lifecycle("env-001", "small")
    assert mock_tools.simulate_rightsizing.called

def test_audit_event_logged_safe(mock_tools):
    agent = RightsizingAgent(mock_tools)
    agent.run_lifecycle("env-001", "small")
    assert mock_tools.write_audit_event.call_count >= 3

def test_agent_trace_length_safe(mock_tools):
    agent = RightsizingAgent(mock_tools)
    trace = agent.run_lifecycle("env-001", "small")
    assert len(trace) == 9  # 9 steps for a safe migration

def test_agent_trace_length_unsafe(mock_tools):
    mock_tools.evaluate_safety.return_value = ({"decision": "DO NOT RIGHTSIZE", "reasons": []}, "Evaluated")
    agent = RightsizingAgent(mock_tools)
    trace = agent.run_lifecycle("env-001", "small")
    assert len(trace) == 6  # 6 steps for unsafe (Blocked)

def test_agent_trace_length_failure(mock_tools):
    mock_tools.run_health_check.return_value = ({"status": "DEGRADED"}, "Failed")
    agent = RightsizingAgent(mock_tools)
    trace = agent.run_lifecycle("env-001", "small")
    assert len(trace) == 10  # 10 steps for post-migration failure and rollback

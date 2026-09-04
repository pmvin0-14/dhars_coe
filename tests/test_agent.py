import os
import sys
import pytest
import pandas as pd
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.agent import RightsizingAgent
from src.agent_tools import AgentTools

@pytest.fixture
def mock_tools():
    tools = MagicMock(spec=AgentTools)
    tools.load_telemetry.return_value = ({"current_instance": "medium", "telemetry_data": None}, "Loaded")
    tools.calculate_baseline.return_value = ({"avg_cpu": 20}, "Baseline")
    
    # Default safe simulation
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

def test_agent_initialization(mock_tools):
    agent = RightsizingAgent(mock_tools)
    assert agent.state == "OBSERVING"
    assert len(agent.trace) == 0

def test_agent_safe_lifecycle(mock_tools):
    agent = RightsizingAgent(mock_tools)
    trace = agent.run_lifecycle("env-001", "small")
    
    assert agent.state == "COMPLETED"
    assert agent.risk_level == "LOW"
    
    states_in_trace = [t['state'] for t in trace]
    assert "OBSERVING" in states_in_trace
    assert "ANALYZING" in states_in_trace
    assert "PLANNING" in states_in_trace
    assert "VALIDATING" in states_in_trace
    assert "EXECUTING" in states_in_trace
    assert "VERIFYING" in states_in_trace

def test_agent_blocked_lifecycle(mock_tools):
    mock_tools.evaluate_safety.return_value = ({"decision": "DO NOT RIGHTSIZE", "reasons": ["Unsafe"]}, "Evaluated")
    agent = RightsizingAgent(mock_tools)
    agent.run_lifecycle("env-001", "small")
    
    assert agent.state == "BLOCKED"

def test_agent_rollback_on_health_failure(mock_tools):
    mock_tools.run_health_check.return_value = ({"status": "DEGRADED"}, "Failed")
    agent = RightsizingAgent(mock_tools)
    agent.run_lifecycle("env-001", "small")
    
    assert agent.state == "ROLLED_BACK"

@pytest.mark.parametrize("peak_cpu, lat, avail, expected_risk", [
    (40, True, True, "LOW"),
    (70, True, True, "MEDIUM"),
    (85, True, True, "HIGH"),
    (95, True, True, "CRITICAL"),
    (40, False, True, "CRITICAL"),
    (40, True, False, "CRITICAL"),
])
def test_agent_risk_scoring(mock_tools, peak_cpu, lat, avail, expected_risk):
    agent = RightsizingAgent(mock_tools)
    sim_res = {
        'peak_cpu': peak_cpu,
        'slo_eval': {'latency_satisfied': lat, 'availability_satisfied': avail}
    }
    assert agent.evaluate_risk(sim_res) == expected_risk

def test_agent_portfolio_mode(mock_tools):
    agent = RightsizingAgent(mock_tools)
    
    # Mocking two environments, one safe, one blocked
    def mock_evaluate_safety(sim_res):
        if hasattr(mock_evaluate_safety, 'called'):
            return ({"decision": "DO NOT RIGHTSIZE", "reasons": []}, "Evaluated")
        mock_evaluate_safety.called = True
        return ({"decision": "SAFE TO RIGHTSIZE", "reasons": []}, "Evaluated")
        
    mock_tools.evaluate_safety.side_effect = mock_evaluate_safety
    
    safe, blocked = agent.analyze_portfolio(["env-1", "env-2"])
    
    assert len(safe) == 1
    assert len(blocked) == 1
    
def test_trace_recording(mock_tools):
    agent = RightsizingAgent(mock_tools)
    agent._record_trace(1, "TEST", "action", "result")
    assert len(agent.trace) == 1
    assert agent.trace[0]['state'] == "TEST"

def test_telemetry_load_failure(mock_tools):
    mock_tools.load_telemetry.return_value = (None, "Failed")
    agent = RightsizingAgent(mock_tools)
    agent.run_lifecycle("env-001", "small")
    assert agent.state == "FAILED"

def test_migration_execution_failure(mock_tools):
    mock_tools.execute_migration.return_value = (False, "Failed")
    agent = RightsizingAgent(mock_tools)
    agent.run_lifecycle("env-001", "small")
    assert agent.state == "FAILED"

def test_tool_selection_safe_path(mock_tools):
    agent = RightsizingAgent(mock_tools)
    agent.run_lifecycle("env-001", "small")
    assert mock_tools.execute_migration.called
    assert mock_tools.run_health_check.called
    assert not mock_tools.execute_rollback.called

def test_tool_selection_unsafe_path(mock_tools):
    mock_tools.evaluate_safety.return_value = ({"decision": "DO NOT RIGHTSIZE", "reasons": ["Unsafe"]}, "Evaluated")
    agent = RightsizingAgent(mock_tools)
    agent.run_lifecycle("env-001", "small")
    assert not mock_tools.execute_migration.called
    assert not mock_tools.run_health_check.called

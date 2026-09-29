import os
import sys
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_loader import DataLoader
from src.simulator import Simulator
from src.mock_infrastructure import LocalInfrastructure
from src.audit_log import AuditLog
from src.orchestrator import MigrationOrchestrator
from src.agent_tools import AgentTools
from src.agent import RightsizingAgent

def run_demo():
    print("Starting Final Demo for Phase 2...")
    data_loader = DataLoader('data')
    envs_df = data_loader.load_environments()
    telemetry_df = data_loader.load_telemetry()
    pricing_df = data_loader.load_pricing()
    
    catalog = {
        'small': {'vcpu': 2, 'memory_gb': 8, 'base_price': 0.05},
        'medium': {'vcpu': 4, 'memory_gb': 16, 'base_price': 0.10},
        'large': {'vcpu': 8, 'memory_gb': 32, 'base_price': 0.20}
    }
    
    sim = Simulator(catalog, pricing_df)
    infra = LocalInfrastructure()
    audit = AuditLog()
    
    for _, row in envs_df.iterrows():
        infra.register_environment(row['environment_id'], row['current_instance_type'])
        
    orchestrator = MigrationOrchestrator(sim, infra, audit)
    agent_tools = AgentTools(sim, infra, audit, data_loader)
    agent = RightsizingAgent(agent_tools)

    results = []

    # Scenario 1: Safe Rightsizing (env-001)
    env1 = 'env-001'
    data1 = telemetry_df[telemetry_df['environment_id'] == env1]
    curr1 = infra.get_instance_state(env1)
    dec1, cand1, res1 = orchestrator.evaluate_all_candidates(env1, curr1, data1)
    if cand1:
        success, msg = orchestrator.execute_migration(env1, curr1, cand1, sim_res=res1, monitoring_scenario="stable")
    else:
        success = False
    
    results.append({'Scenario': '1_Safe', 'Env': env1, 'Decision': dec1, 'Candidate': cand1, 'Success': success})

    # Scenario 2: Unsafe/Blocked (assume env-003 is blocked from review1)
    env2 = 'env-003'
    data2 = telemetry_df[telemetry_df['environment_id'] == env2]
    curr2 = infra.get_instance_state(env2)
    dec2, cand2, res2 = orchestrator.evaluate_all_candidates(env2, curr2, data2)
    results.append({'Scenario': '2_Blocked', 'Env': env2, 'Decision': dec2, 'Candidate': cand2, 'Success': False})

    # Scenario 3: Post-migration degradation + rollback
    env3 = 'env-002' # Try to migrate env-002 safely then fail
    data3 = telemetry_df[telemetry_df['environment_id'] == env3]
    curr3 = infra.get_instance_state(env3)
    dec3, cand3, res3 = orchestrator.evaluate_all_candidates(env3, curr3, data3)
    if cand3:
        success3, msg3 = orchestrator.execute_migration(env3, curr3, cand3, sim_res=res3, monitoring_scenario="persistent_failure")
        rolled_back = infra.get_instance_state(env3) == curr3
    else:
        success3 = False
        rolled_back = False
    results.append({'Scenario': '3_Rollback', 'Env': env3, 'Decision': dec3, 'Candidate': cand3, 'Success': success3, 'RolledBack': rolled_back})

    # Scenario 4: Portfolio
    safe_envs, blocked_envs = agent.analyze_portfolio(['env-004', 'env-005', 'env-006'])
    
    # Scenario 5: Agentic Workflow
    trace = agent.run_lifecycle('env-004', 'small')
    
    df_results = pd.DataFrame(results)
    df_results.to_csv('data/final_experiment_results.csv', index=False)
    
    with open('docs/final_experiment_report.md', 'w') as f:
        f.write("# Final Experiment Report\n\n")
        f.write(df_results.to_csv(index=False))
        f.write("\n\n## Portfolio\n")
        f.write(f"Safe: {len(safe_envs)}, Blocked: {len(blocked_envs)}\n")
        
    print("Demo complete. Results saved.")

if __name__ == "__main__":
    run_demo()

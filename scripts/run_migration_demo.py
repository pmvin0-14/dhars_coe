import os
import sys

# Ensure imports work from parent dir
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_loader import DataLoader
from src.simulator import Simulator
from src.orchestrator import MigrationOrchestrator
from src.mock_infrastructure import LocalInfrastructure
from src.audit_log import AuditLog

def print_header(title):
    print("\n" + "="*50)
    print(f"  {title}")
    print("="*50)

def main():
    print_header("MIGRATION LIFECYCLE DEMO (LOCAL MOCK INFRASTRUCTURE)")
    
    loader = DataLoader('data')
    envs_df = loader.load_environments()
    telemetry_df = loader.load_telemetry()
    pricing_df = loader.load_pricing()

    INSTANCE_CATALOG = {
        'small': {'vcpu': 2, 'memory_gb': 8, 'base_price': 0.05},
        'medium': {'vcpu': 4, 'memory_gb': 16, 'base_price': 0.10},
        'large': {'vcpu': 8, 'memory_gb': 32, 'base_price': 0.20}
    }
    
    simulator = Simulator(INSTANCE_CATALOG, pricing_df)
    infrastructure = LocalInfrastructure()
    audit_log = AuditLog("data/demo_audit_log.csv")
    
    orchestrator = MigrationOrchestrator(simulator, infrastructure, audit_log)

    # Initialize environments
    infrastructure.register_environment('env-007', 'medium')
    infrastructure.register_environment('env-003', 'medium')
    infrastructure.register_environment('env-004', 'medium')

    # FLOW A - SAFE MIGRATION
    print_header("FLOW A: SAFE MIGRATION")
    env_id = 'env-007'
    current_inst = 'medium'
    candidate_inst = 'small'
    env_data = telemetry_df[telemetry_df['environment_id'] == env_id]
    
    print(f"Scenario: {env_id}")
    print(f"Current State: {infrastructure.get_instance_state(env_id)}")
    
    approved, msg, sim_res = orchestrator.pre_migration_check(env_id, current_inst, candidate_inst, env_data)
    print(f"Pre-check Decision: {msg}")
    
    if approved:
        success, exec_msg = orchestrator.execute_migration(env_id, current_inst, candidate_inst, sim_res=sim_res)
        print(f"Migration Execution: {exec_msg}")
        
    print(f"Final State: {infrastructure.get_instance_state(env_id)}")


    # FLOW B - BLOCKED MIGRATION
    print_header("FLOW B: BLOCKED MIGRATION (BURSTY WORKLOAD)")
    env_id = 'env-003'
    current_inst = 'medium'
    candidate_inst = 'small'
    env_data = telemetry_df[telemetry_df['environment_id'] == env_id]
    
    print(f"Scenario: {env_id}")
    print(f"Current State: {infrastructure.get_instance_state(env_id)}")
    
    approved, msg, sim_res = orchestrator.pre_migration_check(env_id, current_inst, candidate_inst, env_data)
    print(f"Pre-check Decision: {msg}")
    
    if approved:
        success, exec_msg = orchestrator.execute_migration(env_id, current_inst, candidate_inst, sim_res=sim_res)
        print(f"Migration Execution: {exec_msg}")
    else:
        print("Migration Execution: BLOCKED by safety gate.")
        
    print(f"Final State: {infrastructure.get_instance_state(env_id)}")


    # FLOW C - ROLLBACK
    print_header("FLOW C: ROLLBACK DUE TO POST-MIGRATION FAILURE")
    env_id = 'env-004'
    current_inst = 'medium'
    candidate_inst = 'small'
    env_data = telemetry_df[telemetry_df['environment_id'] == env_id]
    
    print(f"Scenario: {env_id}")
    print(f"Current State: {infrastructure.get_instance_state(env_id)}")
    
    approved, msg, sim_res = orchestrator.pre_migration_check(env_id, current_inst, candidate_inst, env_data)
    print(f"Pre-check Decision: {msg}")
    
    if approved:
        print("Injecting post-migration failure...")
        success, exec_msg = orchestrator.execute_migration(
            env_id, current_inst, candidate_inst, 
            monitoring_scenario="persistent_failure", sim_res=sim_res
        )
        print(f"Migration Execution: {exec_msg}")
        
    print(f"Final State: {infrastructure.get_instance_state(env_id)}")


if __name__ == "__main__":
    main()

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
from src.data_loader import DataLoader
from src.simulator import Simulator
from scenarios import run_scenario
from src.decision_engine import DecisionEngine

# Recreate catalog for runner
INSTANCE_CATALOG = {
    'small': {'vcpu': 2, 'memory_gb': 8, 'base_price': 0.05},
    'medium': {'vcpu': 4, 'memory_gb': 16, 'base_price': 0.10},
    'large': {'vcpu': 8, 'memory_gb': 32, 'base_price': 0.20}
}

def run_all_experiments():
    loader = DataLoader('data')
    envs_df = loader.load_environments()
    telemetry_df = loader.load_telemetry()
    pricing_df = loader.load_pricing()
    
    sim = Simulator(INSTANCE_CATALOG, pricing_df)
    
    scenarios = ['normal', 'peak', 'bursty']
    results = []
    
    for sc in scenarios:
        env_id = run_scenario(sim, telemetry_df, sc)
        env_data = telemetry_df[telemetry_df['environment_id'] == env_id]
        
        current_instance = envs_df[envs_df['environment_id'] == env_id]['current_instance_type'].iloc[0]
        
        # Determine candidate (cheaper)
        if current_instance == 'large':
            candidate = 'medium'
        elif current_instance == 'medium':
            candidate = 'small'
        else:
            candidate = 'small' # No cheaper option, but we can test
            
        sim_res = sim.run_simulation(env_data, current_instance, candidate)
        decision, reasons = DecisionEngine.evaluate(sim_res)
        
        results.append({
            'scenario': sc,
            'environment_id': env_id,
            'current_instance': current_instance,
            'candidate_instance': candidate,
            'decision': decision,
            'reasons': reasons,
            'sim_res': sim_res
        })
        
    os.makedirs('results', exist_ok=True)
    
    print("=== EXPERIMENT RESULTS ===")
    for r in results:
        print(f"\nScenario: {r['scenario'].upper()} (Env: {r['environment_id']})")
        print(f"Current instance: {r['current_instance']}")
        print(f"Candidate instance: {r['candidate_instance']}\n")
        
        sim_res = r['sim_res']
        cost = sim_res['cost_eval']
        print(f"Baseline monthly cost: ${cost['baseline_monthly_cost']:.2f}")
        print(f"Projected monthly cost: ${cost['simulated_monthly_cost']:.2f}")
        print(f"Cost reduction %: {cost['cost_reduction_pct']:.1f}%\n")
        
        base = sim_res['baseline']
        proj = sim_res['projected_performance']
        
        print(f"Baseline average CPU: {base['mean_cpu']:.1f}%")
        print(f"Projected average CPU: {proj['projected_cpu'].mean():.1f}%\n")
        
        print(f"Baseline peak CPU: {base['peak_cpu']:.1f}%")
        print(f"Projected peak CPU: {proj['projected_cpu'].max():.1f}%\n")
        
        print(f"Baseline peak memory: {base['peak_memory']:.1f}%")
        print(f"Projected peak memory: {proj['projected_memory'].max():.1f}%\n")
        
        slo = sim_res['slo_eval']
        print(f"Baseline P95 latency: {base['p95_latency']:.1f}ms")
        print(f"Projected P95 latency: {slo['projected_p95_latency']:.1f}ms")
        print(f"Latency target: 250.0ms\n")
        
        print(f"Baseline availability: {base['measured_availability']:.2f}%")
        print(f"Projected availability: {slo['projected_availability']:.2f}%")
        print(f"Availability target: 99.90%\n")
        
        print(f"Final decision: {r['decision']}")
        print("Decision reasons:")
        for reason in r['reasons']:
            print(f"- {reason}")

        
if __name__ == "__main__":
    run_all_experiments()

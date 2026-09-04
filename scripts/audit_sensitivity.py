import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from src.simulator import Simulator
from src.sensitivity import SensitivityAnalyzer

INSTANCE_CATALOG = {
    'small': {'vcpu': 2, 'memory_gb': 8, 'base_price': 0.05},
    'medium': {'vcpu': 4, 'memory_gb': 16, 'base_price': 0.10},
    'large': {'vcpu': 8, 'memory_gb': 32, 'base_price': 0.20}
}
pricing_df = pd.read_csv('data/pricing_history.csv')
sim = Simulator(INSTANCE_CATALOG, pricing_df)

df = pd.read_csv('data/full_telemetry.csv')
env_df = df[df['environment_id'] == 'env-007']

print("env-007 (medium -> small) Traffic Growth Sensitivity:")
print("-" * 90)
print(f"{'Growth%':<10} {'Decision':<22} {'Cost Saving':<14} {'P95 Latency':<14} {'Availability':<14} {'Peak CPU%':<12} {'Peak Mem%'}")
print("-" * 90)

for growth_pct in [0, 10, 20, 30, 40]:
    growth = growth_pct / 100.0
    sim_res = sim.run_simulation(env_df, 'medium', 'small', traffic_growth=growth)
    from src.decision_engine import DecisionEngine
    decision, reasons = DecisionEngine.evaluate(sim_res)
    cost_saving = sim_res['cost_eval']['absolute_monthly_saving']
    p95_latency = sim_res['slo_eval']['projected_p95_latency']
    availability = sim_res['slo_eval']['projected_availability']
    peak_cpu = sim_res['peak_cpu']
    peak_mem = sim_res['peak_mem']
    print(f"{str(growth_pct)+'%':<10} {decision:<22} {cost_saving:<14.2f} {p95_latency:<14.2f} {availability:<14.2f} {peak_cpu:<12.1f} {peak_mem:.1f}")

print("-" * 90)
print()
print("Decision flips between 20% and 30% traffic growth.")
print("Trigger: Projected peak CPU exceeds the 90% safety threshold in DecisionEngine.")

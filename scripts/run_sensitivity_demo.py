import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from src.simulator import Simulator
from src.sensitivity import SensitivityAnalyzer

sim = Simulator({
    'small': {'vcpu': 2, 'memory_gb': 8, 'base_price': 0.05},
    'medium': {'vcpu': 4, 'memory_gb': 16, 'base_price': 0.10},
    'large': {'vcpu': 8, 'memory_gb': 32, 'base_price': 0.20}
}, pd.read_csv('data/pricing_history.csv'))

df = pd.read_csv('data/full_telemetry.csv')
env_df = df[df['environment_id'] == 'env-007']

sa = SensitivityAnalyzer(sim)
res = sa.analyze_traffic_growth(env_df, 'medium', 'small')
for r in res:
    print(f"Growth: {r['traffic_growth_pct']}%, Decision: {r['decision']}, P95 Latency: {r['p95_latency']:.2f}, Availability: {r['availability']:.2f}, Savings: {r['cost_saving']:.2f}")

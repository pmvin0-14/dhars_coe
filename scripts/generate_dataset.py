import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration
NUM_ENVIRONMENTS = 100
DAYS_OF_DATA = 30
HOURS = DAYS_OF_DATA * 24
RANDOM_SEED = 42

INSTANCE_CATALOG = {
    'small': {'vcpu': 2, 'memory_gb': 8, 'base_price': 0.05},
    'medium': {'vcpu': 4, 'memory_gb': 16, 'base_price': 0.10},
    'large': {'vcpu': 8, 'memory_gb': 32, 'base_price': 0.20}
}

WORKLOAD_PROFILES = [
    'steady', 'moderate', 'cpu-heavy', 'memory-heavy',
    'low-traffic', 'high-traffic', 'bursty', 'peak-period'
]

def generate_environments():
    np.random.seed(RANDOM_SEED)
    envs = []
    for i in range(1, NUM_ENVIRONMENTS + 1):
        profile = np.random.choice(WORKLOAD_PROFILES)
        
        # Assign instance type based on profile to make it realistic
        if profile in ['high-traffic', 'cpu-heavy', 'memory-heavy']:
            instance = np.random.choice(['medium', 'large'], p=[0.4, 0.6])
        elif profile in ['low-traffic', 'steady']:
            instance = np.random.choice(['small', 'medium'], p=[0.7, 0.3])
        else:
            instance = np.random.choice(['small', 'medium', 'large'])
            
        envs.append({
            'environment_id': f'env-{i:03d}',
            'service_name': f'service-{np.random.choice(["auth", "api", "worker", "frontend", "db"])}-{i}',
            'profile': profile,
            'current_instance_type': instance,
            'vcpu': INSTANCE_CATALOG[instance]['vcpu'],
            'memory_gb': INSTANCE_CATALOG[instance]['memory_gb']
        })
    return pd.DataFrame(envs)

def generate_telemetry(envs_df):
    np.random.seed(RANDOM_SEED)
    start_time = datetime.now() - timedelta(days=DAYS_OF_DATA)
    start_time = start_time.replace(minute=0, second=0, microsecond=0)
    
    timestamps = [start_time + timedelta(hours=i) for i in range(HOURS)]
    
    all_data = []
    
    for _, env in envs_df.iterrows():
        env_id = env['environment_id']
        profile = env['profile']
        instance = env['current_instance_type']
        
        # Base request volume
        if profile == 'high-traffic':
            base_req = np.random.normal(500, 50, HOURS)
        elif profile == 'low-traffic':
            base_req = np.random.normal(50, 10, HOURS)
        else:
            base_req = np.random.normal(200, 30, HOURS)
            
        # Peak periods
        if profile == 'peak-period':
            for i in range(HOURS):
                if 9 <= timestamps[i].hour <= 17:  # Business hours
                    base_req[i] *= 2.5
                    
        # Bursty
        if profile == 'bursty':
            # Low average traffic
            base_req = np.random.normal(50, 10, HOURS)
            # Occasional massive spikes that will saturate a smaller instance
            spike_indices = np.random.choice(HOURS, size=int(HOURS*0.02), replace=False)
            base_req[spike_indices] = np.random.normal(1500, 100, len(spike_indices))
            
        base_req = np.clip(base_req, 10, 3000)
        
        # CPU & Memory Base
        cpu_multiplier = 1.5 if profile == 'cpu-heavy' else 1.0
        mem_multiplier = 1.5 if profile == 'memory-heavy' else 1.0
        
        # Calculate utilization based on requests and instance capacity
        capacity_factor = INSTANCE_CATALOG[instance]['vcpu']
        cpu_util = (base_req / (10 * capacity_factor)) * cpu_multiplier
        # Add random noise
        cpu_util += np.random.normal(0, 5, HOURS)
        
        mem_cap_factor = INSTANCE_CATALOG[instance]['memory_gb']
        # Use 20 as base memory utilization so that downsizing doesn't artificially hit 90%
        mem_util = (base_req / (20 * mem_cap_factor)) * mem_multiplier + np.random.normal(20, 5, HOURS)
        
        cpu_util = np.clip(cpu_util, 1, 100)
        mem_util = np.clip(mem_util, 1, 100)
        
        # Latency Model: Exponential increase near saturation
        base_latency = 50 + np.random.normal(0, 5, HOURS)
        cpu_penalty = np.where(cpu_util > 80, np.clip(cpu_util - 80, 0, None) ** 1.5, 0)
        mem_penalty = np.where(mem_util > 85, np.clip(mem_util - 85, 0, None) ** 1.2, 0)
        latency = base_latency + cpu_penalty + mem_penalty
        
        # Availability Model: Drops when resources are saturated
        availability = np.ones(HOURS) * 100
        violation_mask = (cpu_util > 95) | (mem_util > 95)
        availability[violation_mask] = 100 - np.random.uniform(0.1, 5.0, sum(violation_mask))
        
        df = pd.DataFrame({
            'timestamp': timestamps,
            'environment_id': env_id,
            'instance_type': instance,
            'request_volume': base_req,
            'cpu_utilization_pct': cpu_util,
            'memory_utilization_pct': mem_util,
            'latency_ms': latency,
            'availability_pct': availability
        })
        all_data.append(df)
        
    return pd.concat(all_data, ignore_index=True)

def generate_pricing_history():
    np.random.seed(RANDOM_SEED)
    start_time = datetime.now() - timedelta(days=DAYS_OF_DATA)
    start_time = start_time.replace(minute=0, second=0, microsecond=0)
    timestamps = [start_time + timedelta(hours=i) for i in range(HOURS)]
    
    records = []
    for t in timestamps:
        # Introduce slight price variations over time to prove history is used
        noise = np.random.normal(1.0, 0.02)
        for inst, details in INSTANCE_CATALOG.items():
            records.append({
                'timestamp': t,
                'instance_type': inst,
                'hourly_price': details['base_price'] * noise
            })
    return pd.DataFrame(records)

if __name__ == "__main__":
    os.makedirs('data', exist_ok=True)
    
    print("Generating environments...")
    envs_df = generate_environments()
    envs_df.drop(columns=['profile']).to_csv('data/environments.csv', index=False)
    
    print("Generating telemetry...")
    telemetry_df = generate_telemetry(envs_df)
    
    # Save individual components to match requested structure
    telemetry_df[['timestamp', 'environment_id', 'cpu_utilization_pct']].to_csv('data/cpu_history.csv', index=False)
    telemetry_df[['timestamp', 'environment_id', 'memory_utilization_pct']].to_csv('data/memory_history.csv', index=False)
    telemetry_df[['timestamp', 'environment_id', 'latency_ms']].to_csv('data/latency_history.csv', index=False)
    telemetry_df[['timestamp', 'environment_id', 'request_volume']].to_csv('data/request_history.csv', index=False)
    
    # For baseline and general use, save an availability history too (was implicit but good to have)
    telemetry_df[['timestamp', 'environment_id', 'availability_pct']].to_csv('data/availability_history.csv', index=False)
    
    # Save pricing
    print("Generating pricing history...")
    pricing_df = generate_pricing_history()
    pricing_df.to_csv('data/pricing_history.csv', index=False)
    
    # Save a combined dataset purely for simplified loader if needed
    telemetry_df.to_csv('data/full_telemetry.csv', index=False)
    
    print("Dataset generation complete. Files saved to data/")

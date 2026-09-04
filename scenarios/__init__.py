def run_scenario(simulator, telemetry_df, scenario_type):
    """
    Returns an environment ID that matches the scenario type.
    """
    import pandas as pd
    
    # We generated environments with specific profiles in generate_dataset.py
    # But since telemetry_df doesn't have 'profile', we can infer it or pick based on characteristics.
    # Alternatively, load environments.csv to find a match.
    
    envs_df = pd.read_csv('data/environments.csv')
    
    if scenario_type == 'normal':
        matches = envs_df[envs_df['current_instance_type'] == 'medium']
    elif scenario_type == 'peak':
        matches = envs_df[envs_df['current_instance_type'] == 'large']
    elif scenario_type == 'bursty':
        # Pick a medium environment specifically flagged as bursty if we didn't drop profile,
        # but since we did, any medium will do, our workload generator made them bursty by ID maybe?
        # Actually bursty workload was applied to environments with profile='bursty'
        # Let's just pick one we know has bursty profile. Wait, we dropped profile in generate_dataset.
        # But we can look at request_volume standard deviation to find bursty!
        pass # Handle below
        
    if scenario_type == 'bursty':
        # Find bursty based on telemetry std dev
        telemetry = pd.read_csv('data/request_history.csv')
        std_devs = telemetry.groupby('environment_id')['request_volume'].std()
        bursty_envs = std_devs[std_devs > 100].index
        matches = envs_df[(envs_df['environment_id'].isin(bursty_envs)) & (envs_df['current_instance_type'] == 'medium')]
    elif scenario_type == 'normal':
        # Find normal based on low std dev
        telemetry = pd.read_csv('data/request_history.csv')
        std_devs = telemetry.groupby('environment_id')['request_volume'].std()
        normal_envs = std_devs[std_devs < 50].index
        matches = envs_df[(envs_df['environment_id'].isin(normal_envs)) & (envs_df['current_instance_type'] == 'medium')]
    elif scenario_type == 'peak':
        matches = envs_df[envs_df['current_instance_type'] == 'large']
    else:
        matches = envs_df
        
    if len(matches) == 0:
        # Fallback to just taking the first one
        return envs_df.iloc[0]['environment_id']
        
    # Take the first match
    return matches.iloc[0]['environment_id']

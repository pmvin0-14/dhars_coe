import pandas as pd
import os

class DataLoader:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir

    def load_environments(self):
        return pd.read_csv(os.path.join(self.data_dir, 'environments.csv'))

    def load_telemetry(self):
        # Read separate files and merge
        cpu = pd.read_csv(os.path.join(self.data_dir, 'cpu_history.csv'))
        mem = pd.read_csv(os.path.join(self.data_dir, 'memory_history.csv'))
        lat = pd.read_csv(os.path.join(self.data_dir, 'latency_history.csv'))
        req = pd.read_csv(os.path.join(self.data_dir, 'request_history.csv'))
        avail = pd.read_csv(os.path.join(self.data_dir, 'availability_history.csv'))
        
        # Merge all telemetry
        df = cpu.merge(mem, on=['timestamp', 'environment_id'], how='outer')
        df = df.merge(lat, on=['timestamp', 'environment_id'], how='outer')
        df = df.merge(req, on=['timestamp', 'environment_id'], how='outer')
        df = df.merge(avail, on=['timestamp', 'environment_id'], how='outer')
        
        # Ensure timestamp is datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df

    def load_pricing(self):
        df = pd.read_csv(os.path.join(self.data_dir, 'pricing_history.csv'))
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df

import csv
import os
from datetime import datetime

class AuditLog:
    """
    Lightweight audit log for recording migration lifecycle events.
    """
    def __init__(self, log_path="data/audit_log.csv"):
        self.log_path = log_path
        self._ensure_log_file()

    def _ensure_log_file(self):
        """Creates the log file and header if it doesn't exist."""
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        if not os.path.exists(self.log_path):
            with open(self.log_path, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "environment_id", "current_instance", 
                    "candidate_instance", "event", "reason"
                ])

    def record_event(self, env_id, current_inst, candidate_inst, event, reason=""):
        """Records a migration lifecycle event."""
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        with open(self.log_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, env_id, current_inst, candidate_inst, event, reason
            ])
            
    def get_events_for_env(self, env_id):
        """Retrieves all events for a specific environment."""
        if not os.path.exists(self.log_path):
            return []
            
        events = []
        with open(self.log_path, mode='r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['environment_id'] == env_id:
                    events.append(row)
        return events

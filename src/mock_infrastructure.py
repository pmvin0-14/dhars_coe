class LocalInfrastructure:
    """
    A lightweight local mock infrastructure to maintain the simulated state
    of environments without requiring real cloud deployment.
    """
    def __init__(self):
        self._state = {}

    def register_environment(self, env_id, initial_instance_type):
        """Initialises an environment in the mock infrastructure."""
        self._state[env_id] = {
            "instance_type": initial_instance_type,
            "status": "RUNNING"
        }

    def get_environment(self, env_id):
        """Returns the state of a specific environment."""
        return self._state.get(env_id)

    def validate_environment(self, env_id):
        """Checks if the environment exists and is running."""
        env = self.get_environment(env_id)
        if not env:
            return False, f"Environment {env_id} not found."
        if env["status"] != "RUNNING":
            return False, f"Environment {env_id} is in status {env['status']}, expected RUNNING."
        return True, "Valid"

    def get_instance_state(self, env_id):
        """Returns the current instance type for the environment."""
        env = self.get_environment(env_id)
        return env["instance_type"] if env else None

    def migrate_instance(self, env_id, target_instance_type):
        """Changes the infrastructure state to the target instance type."""
        valid, msg = self.validate_environment(env_id)
        if not valid:
            raise ValueError(msg)
            
        self._state[env_id]["instance_type"] = target_instance_type
        # In a real system status would change to MIGRATING, then back to RUNNING. 
        # For mock simplicity we treat it as an atomic synchronous operation.
        return True

    def rollback_instance(self, env_id, original_instance_type):
        """Reverts the infrastructure state to the original instance type."""
        if env_id not in self._state:
            raise ValueError(f"Environment {env_id} not found for rollback.")
            
        self._state[env_id]["instance_type"] = original_instance_type
        self._state[env_id]["status"] = "RUNNING"
        return True

    def health_check(self, env_id):
        """Simulates an infrastructure-level health check."""
        env = self.get_environment(env_id)
        if not env:
            return False
        return env["status"] == "RUNNING"

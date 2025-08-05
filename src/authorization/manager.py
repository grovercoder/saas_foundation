from typing import List, Dict, Any

class AuthorizationManager:
    def __init__(self):
        self._registered_permissions: List[Dict[str, str]] = []

    def register_permissions(self, permissions: List[Dict[str, str]]):
        """Registers a list of permission dictionaries.

        Each permission dictionary should have 'key', 'name', and 'description' fields.
        The 'key' should be unique and follow the 'object:action' format (e.g., "user:create").
        """
        for permission in permissions:
            if not all(k in permission for k in ["key", "name", "description"]):
                raise ValueError("Each permission must have 'key', 'name', and 'description'.")
            if not isinstance(permission["key"], str) or ":" not in permission["key"]:
                raise ValueError("Permission 'key' must be a string in 'object:action' format.")
            
            # Check for uniqueness of the key
            if any(p["key"] == permission["key"] for p in self._registered_permissions):
                raise ValueError(f"Permission with key '{permission["key"]}' already registered.")

            self._registered_permissions.append(permission)
        

    def get_registered_permissions(self) -> List[Dict[str, str]]:
        """Returns a list of all registered permissions."""
        return self._registered_permissions

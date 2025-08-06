from typing import List, Dict, Any, Optional

class AuthorizationManager:
    def __init__(self, logger: Any):
        self.logger = logger
        self._registered_permissions: List[Dict[str, str]] = []
        self._roles: Dict[str, List[Dict[str, str]]] = {}

    def register_permissions(self, permissions: List[Dict[str, str]]):
        """Registers new permissions with the system."""
        for perm in permissions:
            # Basic validation: ensure 'key' is present
            if "key" not in perm or "name" not in perm or "description" not in perm:
                self.logger.warning(f"Attempted to register permission with missing fields (key, name, or description): {perm}")
                continue

            # Check for duplicate key
            if any(rp["key"] == perm["key"] for rp in self._registered_permissions):
                self.logger.warning(f"Permission with key '{perm['key']}' already registered. Skipping.")
                continue

            # Validate key format (object:action)
            if not isinstance(perm.get("key"), str) or ":" not in perm["key"]:
                self.logger.warning(f"Attempted to register permission with invalid key format: {perm}")
                continue

            self._registered_permissions.append(perm)
            self.logger.info(f"Registered permission: {perm['key']}")

    def get_registered_permissions(self) -> List[Dict[str, str]]:
        """Returns all registered permissions."""
        return self._registered_permissions

    def define_role(self, role_name: str, permissions: List[Dict[str, str]]):
        """Defines a new role and assigns permissions to it."""
        # Ensure all permissions being assigned are actually registered
        for perm_to_assign in permissions:
            if not any(rp["key"] == perm_to_assign["key"] for rp in self._registered_permissions):
                self.logger.warning(f"Attempted to assign unregistered permission '{perm_to_assign.get('key', 'N/A')}' to role '{role_name}'. Skipping.")
                continue
        self._roles[role_name] = permissions
        self.logger.info(f"Defined role '{role_name}' with {len(permissions)} permissions.")

    def get_role_permissions(self, role_name: str) -> List[Dict[str, str]]:
        """Returns the permissions associated with a given role."""
        return self._roles.get(role_name, [])

    def is_authorized(
        self,
        user_roles: List[str],
        action: str,
        resource_type: str,
        resource_id: Optional[Any] = None,
        resource_owner_id: Optional[Any] = None,
        user_id: Optional[Any] = None
    ) -> bool:
        """
        Checks if a user (identified by their roles and optionally user_id) is authorized
        to perform a specific action on a resource.

        Args:
            user_roles: A list of roles assigned to the user.
            action: The action being attempted (e.g., "manage", "create", "edit", "view").
            resource_type: The type of resource (e.g., "subscription_tier", "user", "incident_report").
            resource_id: Optional. The specific ID of the resource instance.
            resource_owner_id: Optional. The ID of the owner of the resource.
            user_id: Optional. The ID of the user attempting the action (for ownership checks).

        Returns:
            True if the user is authorized, False otherwise.
        """
        self.logger.debug(f"Checking authorization for user_roles={user_roles}, action={action}, resource_type={resource_type}, resource_id={resource_id}, resource_owner_id={resource_owner_id}, user_id={user_id}")

        # Default deny principle
        if not user_roles:
            self.logger.debug("User has no roles, denying access.")
            return False

        # Combine permissions from all user's roles
        effective_permissions = []
        for role_name in user_roles:
            effective_permissions.extend(self._roles.get(role_name, []))

        # Evaluate permissions
        for perm in effective_permissions:
            # Check if the permission matches the requested action and resource type
            if perm.get("action") == action and perm.get("resource") == resource_type:
                scope = perm.get("scope")
                perm_id = perm.get("id") # Specific resource ID from permission

                if scope == "global" or scope == "any":
                    self.logger.debug(f"Access granted by global/any permission: {perm}")
                    return True
                elif scope == "own":
                    if user_id is not None and resource_owner_id is not None and user_id == resource_owner_id:
                        self.logger.debug(f"Access granted by 'own' scope permission: {perm}")
                        return True
                elif perm_id is not None and resource_id is not None and perm_id == resource_id:
                    self.logger.debug(f"Access granted by specific resource ID permission: {perm}")
                    return True

        self.logger.debug("No matching permission found, denying access.")
        return False
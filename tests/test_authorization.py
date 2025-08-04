import pytest
from src.authorization.manager import AuthorizationManager

@pytest.fixture
def auth_manager():
    return AuthorizationManager()

def test_register_permissions_success(auth_manager):
    permissions = [
        {"key": "test:read", "name": "Test Read", "description": "Can read test data."},
        {"key": "test:write", "name": "Test Write", "description": "Can write test data."}
    ]
    auth_manager.register_permissions(permissions)
    registered = auth_manager.get_registered_permissions()
    assert len(registered) == 2
    assert registered[0]["key"] == "test:read"
    assert registered[1]["key"] == "test:write"

def test_register_permissions_duplicate_key(auth_manager):
    permissions = [
        {"key": "duplicate:key", "name": "Duplicate Key", "description": "Initial"}
    ]
    auth_manager.register_permissions(permissions)

    with pytest.raises(ValueError, match="Permission with key 'duplicate:key' already registered."):
        auth_manager.register_permissions([
            {"key": "duplicate:key", "name": "Another Duplicate", "description": "Should fail"}
        ])

def test_register_permissions_missing_fields(auth_manager):
    with pytest.raises(ValueError, match="Each permission must have 'key', 'name', and 'description'."):
        auth_manager.register_permissions([
            {"key": "invalid:perm", "name": "Invalid"} # Missing description
        ])

def test_register_permissions_invalid_key_format(auth_manager):
    with pytest.raises(ValueError, match="Permission 'key' must be a string in 'object:action' format."):
        auth_manager.register_permissions([
            {"key": "invalidkeyformat", "name": "Invalid", "description": "Invalid key"}
        ])
    with pytest.raises(ValueError, match="Permission 'key' must be a string in 'object:action' format."):
        auth_manager.register_permissions([
            {"key": 123, "name": "Invalid", "description": "Invalid key type"}
        ])

def test_get_registered_permissions_empty(auth_manager):
    assert auth_manager.get_registered_permissions() == []

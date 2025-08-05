import pytest
from unittest.mock import Mock
from src.authorization.manager import AuthorizationManager

@pytest.fixture
def auth_manager():
    mock_logger = Mock()
    return AuthorizationManager(mock_logger)

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
    assert len(auth_manager.get_registered_permissions()) == 1

    auth_manager.register_permissions([
        {"key": "duplicate:key", "name": "Another Duplicate", "description": "Should fail"}
    ])
    auth_manager.logger.warning.assert_any_call("Permission with key 'duplicate:key' already registered. Skipping.")
    assert len(auth_manager.get_registered_permissions()) == 1

def test_register_permissions_missing_fields(auth_manager):
    permissions = [
        {"name": "Invalid"} # Missing key
    ]
    auth_manager.register_permissions(permissions)
    auth_manager.logger.warning.assert_any_call("Attempted to register permission with missing fields (key, name, or description): {'name': 'Invalid'}")
    assert len(auth_manager.get_registered_permissions()) == 0

def test_register_permissions_invalid_key_format(auth_manager):
    permissions = [
        {"key": "invalidkeyformat", "name": "Invalid", "description": "Invalid key"}
    ]
    auth_manager.register_permissions(permissions)
    auth_manager.logger.warning.assert_any_call("Attempted to register permission with invalid key format: {'key': 'invalidkeyformat', 'name': 'Invalid', 'description': 'Invalid key'}")
    assert len(auth_manager.get_registered_permissions()) == 0

    permissions = [
        {"key": 123, "name": "Invalid", "description": "Invalid key type"}
    ]
    auth_manager.register_permissions(permissions)
    auth_manager.logger.warning.assert_any_call("Attempted to register permission with invalid key format: {'key': 123, 'name': 'Invalid', 'description': 'Invalid key type'}")
    assert len(auth_manager.get_registered_permissions()) == 0

def test_get_registered_permissions_empty(auth_manager):
    assert auth_manager.get_registered_permissions() == []

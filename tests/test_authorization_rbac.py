import pytest
from unittest.mock import Mock
from src.authorization.manager import AuthorizationManager

@pytest.fixture
def mock_logger():
    return Mock()

@pytest.fixture
def auth_manager_rbac(mock_logger):
    manager = AuthorizationManager(mock_logger)

    # Register all possible permissions
    manager.register_permissions([
        {"key": "manage_subscription_tiers", "action": "manage", "resource": "subscription_tier", "scope": "global"},
        {"key": "manage_own_users", "action": "manage", "resource": "user", "scope": "own"},
        {"key": "do_feature_x", "action": "do", "resource": "feature_x", "scope": "global"},
        {"key": "manage_all_incident_reports", "action": "manage", "resource": "incident_report", "scope": "global"},
        {"key": "create_incident_report", "action": "create", "resource": "incident_report", "scope": "global"},
        {"key": "edit_own_incident_report", "action": "edit", "resource": "incident_report", "scope": "own"},
        {"key": "edit_incident_report_55", "action": "edit", "resource": "incident_report", "id": 55},
    ])

    # Define roles
    manager.define_role("SAAS_Admin", [
        {"key": "manage_subscription_tiers", "action": "manage", "resource": "subscription_tier", "scope": "global"},
    ])
    manager.define_role("Account_Admin", [
        {"key": "manage_own_users", "action": "manage", "resource": "user", "scope": "own"},
    ])
    manager.define_role("Normal_User", [
        {"key": "do_feature_x", "action": "do", "resource": "feature_x", "scope": "global"},
        {"key": "create_incident_report", "action": "create", "resource": "incident_report", "scope": "global"},
        {"key": "edit_own_incident_report", "action": "edit", "resource": "incident_report", "scope": "own"},
    ])
    manager.define_role("Safety_Officer", [
        {"key": "manage_all_incident_reports", "action": "manage", "resource": "incident_report", "scope": "global"},
    ])
    manager.define_role("SpecialX", [
        {"key": "edit_incident_report_55", "action": "edit", "resource": "incident_report", "id": 55},
    ])

    return manager

# Test Cases

def test_saas_admin_can_manage_subscription_tiers(auth_manager_rbac):
    user_roles = ["SAAS_Admin"]
    assert auth_manager_rbac.is_authorized(user_roles, "manage", "subscription_tier") is True
    assert auth_manager_rbac.is_authorized(user_roles, "manage", "user") is False # Should not manage users

def test_account_admin_can_manage_own_users(auth_manager_rbac):
    user_roles = ["Account_Admin"]
    # User 1 owns resource 1
    assert auth_manager_rbac.is_authorized(user_roles, "manage", "user", resource_id=1, resource_owner_id=1, user_id=1) is True
    # User 1 does not own resource 2
    assert auth_manager_rbac.is_authorized(user_roles, "manage", "user", resource_id=2, resource_owner_id=1, user_id=2) is False
    # No user_id provided
    assert auth_manager_rbac.is_authorized(user_roles, "manage", "user", resource_id=1, resource_owner_id=1) is False

def test_normal_user_can_do_feature_x(auth_manager_rbac):
    user_roles = ["Normal_User"]
    assert auth_manager_rbac.is_authorized(user_roles, "do", "feature_x") is True
    assert auth_manager_rbac.is_authorized(user_roles, "manage", "subscription_tier") is False

def test_safety_officer_can_manage_all_incident_reports(auth_manager_rbac):
    user_roles = ["Safety_Officer"]
    assert auth_manager_rbac.is_authorized(user_roles, "manage", "incident_report", resource_id=1) is True
    assert auth_manager_rbac.is_authorized(user_roles, "manage", "incident_report", resource_id=999) is True
    assert auth_manager_rbac.is_authorized(user_roles, "do", "feature_x") is False

def test_normal_user_can_create_incident_reports(auth_manager_rbac):
    user_roles = ["Normal_User"]
    assert auth_manager_rbac.is_authorized(user_roles, "create", "incident_report") is True

def test_normal_user_can_edit_own_incident_reports(auth_manager_rbac):
    user_roles = ["Normal_User"]
    # User 1 owns incident report 1
    assert auth_manager_rbac.is_authorized(user_roles, "edit", "incident_report", resource_id=1, resource_owner_id=1, user_id=1) is True
    # User 1 does not own incident report 2
    assert auth_manager_rbac.is_authorized(user_roles, "edit", "incident_report", resource_id=2, resource_owner_id=1, user_id=2) is False

def test_special_x_can_edit_incident_report_55(auth_manager_rbac):
    user_roles = ["SpecialX"]
    assert auth_manager_rbac.is_authorized(user_roles, "edit", "incident_report", resource_id=55) is True
    assert auth_manager_rbac.is_authorized(user_roles, "edit", "incident_report", resource_id=56) is False
    assert auth_manager_rbac.is_authorized(user_roles, "manage", "subscription_tier") is False

def test_user_with_multiple_roles(auth_manager_rbac):
    user_roles = ["Normal_User", "SAAS_Admin"]
    assert auth_manager_rbac.is_authorized(user_roles, "manage", "subscription_tier") is True
    assert auth_manager_rbac.is_authorized(user_roles, "create", "incident_report") is True
    assert auth_manager_rbac.is_authorized(user_roles, "manage", "user", resource_id=1, resource_owner_id=1, user_id=1) is False # SAAS Admin doesn't get Account Admin perms

def test_unauthorized_action(auth_manager_rbac):
    user_roles = ["Normal_User"]
    assert auth_manager_rbac.is_authorized(user_roles, "delete", "feature_x") is False

def test_no_roles(auth_manager_rbac):
    user_roles = []
    assert auth_manager_rbac.is_authorized(user_roles, "do", "feature_x") is False

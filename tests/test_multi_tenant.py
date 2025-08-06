import pytest
import os
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import Mock

from saas_foundation.datastore.manager import DatastoreManager
from saas_foundation.datastore.database import get_db_connection, execute_query
from saas_foundation.multi_tenant.manager import MultiTenantManager, MODULE_PERMISSIONS
from saas_foundation.authorization.manager import AuthorizationManager # Import AuthorizationManager
from saas_foundation.multi_tenant.models import Account, User

@pytest.fixture
def mock_logger():
    return Mock()

# Use an in-memory database for testing
@pytest.fixture(scope="function")
def db_connection(mock_logger):
    original_db_path = os.getenv("DB_PATH")
    original_db_name = os.getenv("DB_NAME")

    os.environ["DB_PATH"] = "" # Set DB_PATH to empty for in-memory tests
    os.environ["DB_NAME"] = ":memory:"

    conn = get_db_connection(mock_logger)
    yield conn
    conn.close()

    if original_db_path is not None:
        os.environ["DB_PATH"] = original_db_path
    else:
        del os.environ["DB_PATH"]

    if original_db_name is not None:
        os.environ["DB_NAME"] = original_db_name
    else:
        del os.environ["DB_NAME"]

    

@pytest.fixture(scope="function")
def setup_multi_tenant_db(db_connection, mock_logger):
    # Ensure tables are clean before each test
    execute_query("DROP TABLE IF EXISTS users", conn=db_connection, logger=mock_logger)
    execute_query("DROP TABLE IF EXISTS accounts", conn=db_connection, logger=mock_logger)

    # Initialize DatastoreManager with multi_tenant entities
    datastore_manager = DatastoreManager(mock_logger, [Account, User], connection=db_connection)
    yield datastore_manager

@pytest.fixture(scope="function")
def auth_manager(mock_logger):
    return AuthorizationManager(mock_logger)

@pytest.fixture(scope="function")
def multi_tenant_manager(setup_multi_tenant_db, auth_manager, mock_logger):
    return MultiTenantManager(mock_logger, setup_multi_tenant_db, auth_manager)

@pytest.fixture(scope="function")
def multi_tenant_manager_no_auth(setup_multi_tenant_db, mock_logger):
    return MultiTenantManager(mock_logger, setup_multi_tenant_db)


def test_multi_tenant_manager_registers_permissions(auth_manager, setup_multi_tenant_db, mock_logger):
    # Create manager with auth_manager
    MultiTenantManager(mock_logger, setup_multi_tenant_db, auth_manager)
    registered_permissions = auth_manager.get_registered_permissions()
    assert len(registered_permissions) == len(MODULE_PERMISSIONS)
    for perm in MODULE_PERMISSIONS:
        assert perm in registered_permissions

def test_multi_tenant_manager_no_auth_registration(setup_multi_tenant_db, mock_logger):
    # Ensure no permissions are registered if auth_manager is not provided
    fresh_auth_manager = AuthorizationManager(mock_logger)
    # Initialize MultiTenantManager without passing an authorization_manager
    MultiTenantManager(mock_logger, setup_multi_tenant_db, authorization_manager=None)
    assert len(fresh_auth_manager.get_registered_permissions()) == 0


def test_create_account(multi_tenant_manager):
    account_name = "Test Account"
    account = multi_tenant_manager.create_account(account_name)
    assert isinstance(account, Account)
    assert account.name == account_name

    retrieved_account = multi_tenant_manager.get_account_by_id(account.id)
    assert retrieved_account == account


def test_create_user(multi_tenant_manager):
    account = multi_tenant_manager.create_account("User Account")
    username = "testuser"
    password = "password123"
    user = multi_tenant_manager.create_user(account.id, username, password)

    assert isinstance(user, User)
    assert user.username == username
    assert user.account_id == account.id
    assert user.password_hash is not None

    retrieved_user = multi_tenant_manager.get_user_by_id(user.id)
    assert retrieved_user.username == username
    assert retrieved_user.account_id == account.id


def test_authenticate_user(multi_tenant_manager):
    account = multi_tenant_manager.create_account("Auth Account")
    username = "authuser"
    password = "authpassword"
    multi_tenant_manager.create_user(account.id, username, password)

    authenticated_user = multi_tenant_manager.authenticate_user(username, password)
    assert authenticated_user is not None
    assert authenticated_user.username == username

    failed_auth = multi_tenant_manager.authenticate_user(username, "wrongpassword")
    assert failed_auth is None

    failed_auth_user = multi_tenant_manager.authenticate_user("nonexistent", password)
    assert failed_auth_user is None


def test_reset_token_flow(multi_tenant_manager):
    account = multi_tenant_manager.create_account("Reset Account")
    username = "resetuser"
    password = "resetpassword"
    user = multi_tenant_manager.create_user(account.id, username, password)

    # Set token
    token = multi_tenant_manager.generate_reset_token(username)
    assert token is not None

    # Reset password
    new_password = "newresetpassword"
    assert multi_tenant_manager.reset_password(username, token, new_password)

    # Check if token is cleared and new password works
    retrieved_user_after_reset = multi_tenant_manager.get_user_by_id(user.id)
    assert retrieved_user_after_reset.reset_token is None
    assert retrieved_user_after_reset.reset_token_created_at is None

    authenticated_user = multi_tenant_manager.authenticate_user(username, new_password)
    assert authenticated_user is not None


def test_get_user_by_username(multi_tenant_manager):
    account = multi_tenant_manager.create_account("Lookup Account")
    username = "lookupuser"
    password = "lookuppassword"
    multi_tenant_manager.create_user(account.id, username, password)

    user = multi_tenant_manager.get_user_by_username(username)
    assert user is not None
    assert user.username == username
    assert user.account_id == account.id

    non_existent_user = multi_tenant_manager.get_user_by_username("nonexistentuser")
    assert non_existent_user is None


def test_create_user_invalid_account_id(multi_tenant_manager):
    username = "invaliduser"
    password = "password"
    with pytest.raises(ValueError, match="Invalid account ID provided."):
        multi_tenant_manager.create_user(99999, username, password)

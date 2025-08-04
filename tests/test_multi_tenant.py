import pytest
import os
import sqlite3
from datetime import datetime, timedelta

from src.datastore.manager import DatastoreManager
from src.datastore.database import get_db_connection, execute_query
from src.multi_tenant.manager import MultiTenantManager, multi_tenant_entity_definitions
from src.multi_tenant.models import Account, User

# Use an in-memory database for testing
@pytest.fixture(scope="function")
def db_connection():
    original_db_url = os.getenv("DATABASE_URL")
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    conn = get_db_connection()
    yield conn
    conn.close()

    if original_db_url is not None:
        os.environ["DATABASE_URL"] = original_db_url
    else:
        del os.environ["DATABASE_URL"]

@pytest.fixture(scope="function")
def setup_multi_tenant_db(db_connection):
    # Ensure tables are clean before each test
    execute_query("DROP TABLE IF EXISTS users")
    execute_query("DROP TABLE IF EXISTS accounts")

    # Initialize DatastoreManager with multi_tenant entities
    datastore_manager = DatastoreManager(multi_tenant_entity_definitions)
    yield datastore_manager

@pytest.fixture(scope="function")
def multi_tenant_manager(setup_multi_tenant_db):
    return MultiTenantManager(setup_multi_tenant_db)


def test_create_account(multi_tenant_manager):
    account_name = "Test Account"
    account = multi_tenant_manager.create_account(account_name)
    assert isinstance(account, Account)
    assert account.name == account_name
    assert account.id is not None

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
    assert user.id is not None

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
    token = multi_tenant_manager.set_reset_token(user.id)
    assert token is not None
    retrieved_user = multi_tenant_manager.get_user_by_id(user.id)
    assert retrieved_user.reset_token == token
    assert retrieved_user.reset_token_created_at is not None

    # Verify token
    assert multi_tenant_manager.verify_reset_token(user.id, token)

    # Verify with wrong token
    assert not multi_tenant_manager.verify_reset_token(user.id, "wrongtoken")

    # Test token expiry (simulate time passing)
    # Note: This is a bit tricky with datetime.now(). For a real test, consider mocking datetime.
    # For simplicity, we'll just test the expiry logic with a very short expiry.
    old_expiry = multi_tenant_manager.verify_reset_token(user.id, token, expiry_minutes=0) # Should expire immediately
    assert not old_expiry

    # Reset password
    new_password = "newresetpassword"
    assert multi_tenant_manager.reset_password(user.id, new_password, token)

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
        multi_tenant_manager.create_user("invalidhashid", username, password)

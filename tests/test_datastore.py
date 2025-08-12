import pytest
import os
import sqlite3
from unittest.mock import Mock
from saas_foundation.datastore.database import (
    get_db_connection,
    execute_query,
    fetch_one,
    fetch_all,
)
from saas_foundation.datastore.schema import create_tables_from_entity_definitions
from saas_foundation.datastore.dao import BaseDAO
from saas_foundation.datastore.manager import (
    DatastoreManager,
)  # Added import for DatastoreManager
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TestUser:
    id: int
    name: str
    email: str


@dataclass
class TestProduct:
    id: int
    product_name: str
    price: float


@pytest.fixture
def mock_logger():
    return Mock()


# Use an in-memory database for testing
@pytest.fixture(scope="function")
def db_connection(mock_logger):
    # Temporarily set environment variables for testing
    original_db_name = os.getenv("DB_NAME")
    original_db_path = os.getenv("DB_PATH")

    os.environ["DB_NAME"] = ":memory:"
    os.environ["DB_PATH"] = ""  # Set DB_PATH to empty for in-memory tests

    conn = get_db_connection(mock_logger)
    yield conn
    conn.close()

    # Restore original environment variables
    if original_db_name is not None:
        os.environ["DB_NAME"] = original_db_name
    else:
        del os.environ["DB_NAME"]

    if original_db_path is not None:
        os.environ["DB_PATH"] = original_db_path
    else:
        del os.environ["DB_PATH"]


@pytest.fixture(scope="function")
def datastore_manager(datastore_manager_with_models):
    return datastore_manager_with_models


@pytest.fixture(scope="function")
def datastore_manager_with_models(db_connection, mock_logger):
    # Ensure tables are clean before each test
    db_connection.execute("DROP TABLE IF EXISTS testusers")
    db_connection.execute("DROP TABLE IF EXISTS testproducts")
    # Initialize DatastoreManager with models and pass the connection
    manager = DatastoreManager(
        mock_logger, [TestUser, TestProduct], connection=db_connection
    )
    return manager


def test_db_connection(db_connection):
    assert db_connection is not None
    assert isinstance(db_connection, sqlite3.Connection)


def test_create_tables(datastore_manager_with_models, db_connection):
    cursor = db_connection.cursor()
    cursor.execute("PRAGMA table_info(testusers)")
    columns = [col[1] for col in cursor.fetchall()]
    assert "id" in columns
    assert "name" in columns
    assert "email" in columns


def test_insert_and_get_user(datastore_manager_with_models):
    user_data = {"name": "Test User", "email": "test@example.com"}
    int_id = datastore_manager_with_models.insert("testusers", user_data)
    assert int_id is not None
    assert isinstance(int_id, int)  # Should be an integer ID

    retrieved_user = datastore_manager_with_models.get_by_id("testusers", int_id)
    assert retrieved_user is not None
    assert retrieved_user["name"] == "Test User"
    assert retrieved_user["email"] == "test@example.com"
    assert retrieved_user["id"] == int_id  # ID should be the integer ID


def test_get_all_users(datastore_manager_with_models):
    datastore_manager_with_models.insert(
        "testusers", {"name": "User 1", "email": "user1@example.com"}
    )
    datastore_manager_with_models.insert(
        "testusers", {"name": "User 2", "email": "user2@example.com"}
    )

    users = datastore_manager_with_models.get_all("testusers")
    assert len(users) == 2
    assert all(
        isinstance(user["id"], int) for user in users
    )  # All IDs should be integer IDs


def test_update_user(datastore_manager_with_models):
    int_id = datastore_manager_with_models.insert(
        "testusers", {"name": "Old Name", "email": "old@example.com"}
    )
    datastore_manager_with_models.update("testusers", int_id, {"name": "New Name"})

    updated_user = datastore_manager_with_models.get_by_id("testusers", int_id)
    assert updated_user["name"] == "New Name"
    assert updated_user["email"] == "old@example.com"


def test_delete_user(datastore_manager_with_models):
    int_id = datastore_manager_with_models.insert(
        "testusers", {"name": "Delete Me", "email": "delete@example.com"}
    )
    datastore_manager_with_models.delete("testusers", int_id)

    deleted_user = datastore_manager_with_models.get_by_id("testusers", int_id)
    assert deleted_user is None


def test_datastore_manager_initialization(db_connection, mock_logger):
    manager = DatastoreManager(
        mock_logger, [TestUser, TestProduct], connection=db_connection
    )
    assert manager.get_dao("testusers") is not None
    assert isinstance(manager.get_dao("testusers"), BaseDAO)
    assert manager.get_dao("testproducts") is not None

    # Test that tables are created
    cursor = db_connection.cursor()
    cursor.execute("PRAGMA table_info(testusers)")
    assert len(cursor.fetchall()) > 0
    cursor.execute("PRAGMA table_info(testproducts)")
    assert len(cursor.fetchall()) > 0


def test_datastore_manager_register_entities(
    datastore_manager_with_models, db_connection
):
    manager = datastore_manager_with_models

    @dataclass
    class NewEntity1:
        id: int
        hash_id: str
        name: str

    @dataclass
    class NewEntity2:
        id: int
        hash_id: str
        value: int

    manager.register_dataclass_models([NewEntity1, NewEntity2])

    assert manager.get_dao("newentity1s") is not None
    assert manager.get_dao("newentity2s") is not None

    # Verify tables are created
    cursor = db_connection.cursor()
    cursor.execute("PRAGMA table_info(newentity1s)")
    assert len(cursor.fetchall()) > 0
    cursor.execute("PRAGMA table_info(newentity2s)")
    assert len(cursor.fetchall()) > 0


def test_datastore_manager_get_dao_invalid_entity(datastore_manager_with_models):
    manager = datastore_manager_with_models
    with pytest.raises(
        ValueError, match="DAO for entity 'non_existent_entity' not found."
    ):
        manager.get_dao("non_existent_entity")

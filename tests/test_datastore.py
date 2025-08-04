import pytest
import os
import sqlite3
from hashids import Hashids # Added import for Hashids
from src.datastore.database import get_db_connection, execute_query, fetch_one, fetch_all
from src.datastore.schema import create_tables_from_entity_definitions
from src.datastore.dao import BaseDAO, hashids # Import hashids directly for testing encoding/decoding
from src.datastore.manager import DatastoreManager # Added import for DatastoreManager

# Use an in-memory database for testing
@pytest.fixture(scope="function")
def db_connection():
    # Temporarily set DATABASE_URL to an in-memory database
    original_db_url = os.getenv("DATABASE_URL")
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    conn = get_db_connection()
    yield conn
    conn.close()

    # Restore original DATABASE_URL
    if original_db_url is not None:
        os.environ["DATABASE_URL"] = original_db_url
    else:
        del os.environ["DATABASE_URL"]

@pytest.fixture(scope="function")
def setup_db(db_connection):
    # Define a simple entity for testing
    entity_definitions = {
        "test_users": {
            "name": "TEXT NOT NULL",
            "email": "TEXT UNIQUE NOT NULL"
        }
    }
    # Ensure table is clean before each test
    execute_query("DROP TABLE IF EXISTS test_users") # Added: Drop table before creation
    create_tables_from_entity_definitions(entity_definitions)
    yield

@pytest.fixture(scope="function")
def user_dao():
    return BaseDAO("test_users")


def test_db_connection(db_connection):
    assert db_connection is not None
    assert isinstance(db_connection, sqlite3.Connection)


def test_create_tables(setup_db, db_connection):
    cursor = db_connection.cursor()
    cursor.execute("PRAGMA table_info(test_users)")
    columns = [col[1] for col in cursor.fetchall()]
    assert "id" in columns
    assert "name" in columns
    assert "email" in columns


def test_insert_and_get_user(setup_db, user_dao):
    user_data = {"name": "Test User", "email": "test@example.com"}
    hash_id = user_dao.insert(user_data)
    assert hash_id is not None
    assert isinstance(hash_id, str) # Should be a hashid string

    retrieved_user = user_dao.get_by_id(hash_id)
    assert retrieved_user is not None
    assert retrieved_user["name"] == "Test User"
    assert retrieved_user["email"] == "test@example.com"
    assert retrieved_user["id"] == hash_id # ID should be the hashid


def test_get_all_users(setup_db, user_dao):
    user_dao.insert({"name": "User 1", "email": "user1@example.com"})
    user_dao.insert({"name": "User 2", "email": "user2@example.com"})

    users = user_dao.get_all()
    assert len(users) == 2
    assert all(isinstance(user["id"], str) for user in users) # All IDs should be hashids


def test_update_user(setup_db, user_dao):
    hash_id = user_dao.insert({"name": "Old Name", "email": "old@example.com"})
    user_dao.update(hash_id, {"name": "New Name"})

    updated_user = user_dao.get_by_id(hash_id)
    assert updated_user["name"] == "New Name"
    assert updated_user["email"] == "old@example.com"


def test_delete_user(setup_db, user_dao):
    hash_id = user_dao.insert({"name": "Delete Me", "email": "delete@example.com"})
    user_dao.delete(hash_id)

    deleted_user = user_dao.get_by_id(hash_id)
    assert deleted_user is None


def test_datastore_manager_initialization(setup_db):
    entity_definitions = {
        "manager_users": {
            "name": "TEXT NOT NULL",
            "email": "TEXT UNIQUE NOT NULL"
        },
        "manager_products": {
            "product_name": "TEXT NOT NULL",
            "price": "REAL"
        }
    }
    manager = DatastoreManager(entity_definitions)

    assert manager.get_dao("manager_users") is not None
    assert isinstance(manager.get_dao("manager_users"), BaseDAO)
    assert manager.get_dao("manager_products") is not None

    # Test that tables are created
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(manager_users)")
    assert len(cursor.fetchall()) > 0
    cursor.execute("PRAGMA table_info(manager_products)")
    assert len(cursor.fetchall()) > 0
    conn.close()


def test_datastore_manager_register_entities(setup_db):
    initial_entities = {"initial_entity": {"field1": "TEXT"}}
    manager = DatastoreManager(initial_entities)
    assert manager.get_dao("initial_entity") is not None

    new_entities = {
        "new_entity_1": {"name": "TEXT"},
        "new_entity_2": {"value": "INTEGER"}
    }
    manager.register_entity_definitions(new_entities)

    assert manager.get_dao("new_entity_1") is not None
    assert manager.get_dao("new_entity_2") is not None

    # Verify tables are created
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(new_entity_1)")
    assert len(cursor.fetchall()) > 0
    cursor.execute("PRAGMA table_info(new_entity_2)")
    assert len(cursor.fetchall()) > 0
    conn.close()


def test_datastore_manager_get_dao_invalid_entity(setup_db):
    entity_definitions = {"some_entity": {"name": "TEXT"}}
    manager = DatastoreManager(entity_definitions)
    with pytest.raises(ValueError, match="DAO for entity 'non_existent_entity' not found."):
        manager.get_dao("non_existent_entity")


def test_hashid_encoding_decoding():
    # Test direct hashids encoding/decoding
    original_id = 123
    encoded_id = hashids.encode(original_id)
    decoded_id = hashids.decode(encoded_id)
    assert decoded_id[0] == original_id

    # Test with a different salt (should produce different hash)
    temp_hashids = Hashids(salt="another_salt", min_length=8)
    another_encoded_id = temp_hashids.encode(original_id)
    assert encoded_id != another_encoded_id


def test_insert_invalid_hashid(setup_db, user_dao):
    with pytest.raises(ValueError, match="Invalid hash ID provided for update."):
        user_dao.update("invalid_hash", {"name": "Should Fail"})

    with pytest.raises(ValueError, match="Invalid hash ID provided for delete."):
        user_dao.delete("invalid_hash")

from src.datastore.schema import create_tables_from_entity_definitions
from src.datastore.dao import BaseDAO, hashids # Import hashids for encoding/decoding

class DatastoreManager:
    def __init__(self, entity_definitions):
        self.entity_definitions = entity_definitions
        self._daos = {}
        self._initialize_datastore()

    def _encode_id(self, int_id):
        return hashids.encode(int_id)

    def _decode_id(self, hash_id):
        decoded = hashids.decode(hash_id)
        return decoded[0] if decoded else None

    def _initialize_datastore(self):
        # Create tables based on entity definitions
        create_tables_from_entity_definitions(self.entity_definitions)
        # Create DAO instances for each entity
        for entity_name in self.entity_definitions.keys():
            self._daos[entity_name] = BaseDAO(entity_name)

    def register_entity_definitions(self, new_entity_definitions):
        """Registers new entity definitions and updates the datastore."""
        print("Registering new entity definitions...")
        # Merge new definitions with existing ones
        self.entity_definitions.update(new_entity_definitions)
        # Create tables for newly registered entities
        create_tables_from_entity_definitions(new_entity_definitions)
        # Create DAO instances for newly registered entities
        for entity_name in new_entity_definitions.keys():
            if entity_name not in self._daos:
                self._daos[entity_name] = BaseDAO(entity_name)
            else:
                print(f"DAO for '{entity_name}' already exists. Skipping re-creation.")

    def get_dao(self, entity_name):
        """Returns the DAO instance for a given entity name."""
        if entity_name not in self._daos:
            raise ValueError(f"DAO for entity '{entity_name}' not found.")
        return self._daos[entity_name]

    # Optional: Provide direct access properties for common DAOs
    @property
    def users(self):
        return self.get_dao("users")

    @property
    def products(self):
        return self.get_dao("products")

from src.datastore.schema import create_tables_from_entity_definitions
from src.datastore.dao import BaseDAO

import os
from dataclasses import is_dataclass, fields, MISSING


from typing import Any, List, Dict, Type, Optional, Union, get_origin, get_args
from types import UnionType
from datetime import datetime

class DatastoreManager:
    def __init__(self, models: List[Type[Any]] | None = None):
        self.entity_definitions = {}
        self._daos = {}
        if models:
            print(f"DatastoreManager: Initializing with models: {[m.__name__ for m in models]}")
            self.register_dataclass_models(models)
        print(f"DatastoreManager: After register_dataclass_models, entity_definitions keys: {self.entity_definitions.keys()}")
        self._initialize_datastore()
        print(f"DatastoreManager: After _initialize_datastore, _daos keys: {self._daos.keys()}")

    

    def _initialize_datastore(self):
        print(f"DatastoreManager._initialize_datastore: entity_definitions keys: {self.entity_definitions.keys()}")
        # Create tables based on entity definitions
        create_tables_from_entity_definitions(self.entity_definitions)
        # Create DAO instances for each entity
        for entity_name in self.entity_definitions.keys():
            self._daos[entity_name] = BaseDAO(entity_name)
        print(f"DatastoreManager._initialize_datastore: Populated _daos with keys: {self._daos.keys()}")

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

    def _get_column_type(self, python_type: Type) -> str:
        """Maps Python types to SQLite column types."""
        print(f"Debug: _get_column_type received type: {python_type}")
        # Handle Optional types
        if get_origin(python_type) is Union or get_origin(python_type) is UnionType:
            # Extract the actual type from Optional or Union
            args = get_args(python_type)
            python_type = next((arg for arg in args if arg is not type(None)), None)
            if python_type is None:
                raise ValueError(f"Could not determine base type from Optional or Union: {args}")
            print(f"Debug: _get_column_type after Optional/Union handling: {python_type}")

        # Handle generic types like List and Dict
        if get_origin(python_type) in (list, dict):
            return "TEXT"  # Store lists/dicts as JSON strings

        # Handle Any type
        if python_type is Any:
            return "TEXT"

        # Ensure python_type is a concrete type before proceeding
        if not isinstance(python_type, type):
            raise ValueError(f"Resolved type is not a concrete type: {python_type}")

        if python_type is str:
            return "TEXT"
        elif python_type is int:
            return "INTEGER"
        elif python_type is float:
            return "REAL"
        elif python_type is bool:
            return "INTEGER"  # SQLite stores booleans as 0 or 1
        elif python_type is datetime:
            return "TEXT"  # Store datetime as ISO 8601 string
        else:
            raise ValueError(f"Unsupported Python type for schema generation: {python_type}")

    def register_dataclass_models(self, models: List[Type[Any]]):
        """Registers dataclass models and generates entity definitions."""
        new_entity_definitions = {}
        for model in models:
            if not is_dataclass(model):
                raise TypeError(f"Provided object {model.__name__} is not a dataclass.")

            table_name = model.__name__.lower() + "s"  # Simple pluralization
            entity_schema = {}
            for field_info in fields(model):
                print(f"Debug: Processing field: {field_info.name}")
                print(f"Debug:   Type: {field_info.type}")
                print(f"Debug:   Origin: {get_origin(field_info.type)}")
                print(f"Debug:   Args: {get_args(field_info.type)}")
                print(f"Debug:   Default: {field_info.default}")
                print(f"Debug:   Default Factory: {field_info.default_factory}")
                if field_info.name == "id":
                    continue  # 'id' is handled implicitly as PRIMARY KEY AUTOINCREMENT
                
                column_type = self._get_column_type(field_info.type)
                print(f"Debug:   Column Type (before NOT NULL): {column_type}")
                
                # Add default values for created_at and updated_at
                if field_info.name == "created_at":
                    entity_schema[field_info.name] = f"{column_type} DEFAULT CURRENT_TIMESTAMP"
                elif field_info.name == "updated_at":
                    entity_schema[field_info.name] = f"{column_type} DEFAULT CURRENT_TIMESTAMP"
                
                else:
                    entity_schema[field_info.name] = column_type
                    # Add NOT NULL constraint if not Optional and not a default factory
                    is_optional = get_origin(field_info.type) is Union or get_origin(field_info.type) is Optional or (get_origin(field_info.type) is UnionType and type(None) in get_args(field_info.type))
                    print(f"Debug:   Is Optional: {is_optional}")
                    if not is_optional:
                        entity_schema[field_info.name] += " NOT NULL"
                print(f"Debug:   Final Schema Entry: {field_info.name}: {entity_schema[field_info.name]}")

            new_entity_definitions[table_name] = entity_schema
        
        print(f"DatastoreManager.register_dataclass_models: Generated new_entity_definitions keys: {new_entity_definitions.keys()}")
        self.register_entity_definitions(new_entity_definitions)
        print(f"DatastoreManager.register_dataclass_models: After register_entity_definitions, self.entity_definitions keys: {self.entity_definitions.keys()}")

    def insert(self, entity_name: str, data: Dict[str, Any]) -> int:
        dao = self.get_dao(entity_name)
        int_id = dao.insert(data)
        return int_id

    def get_by_id(self, entity_name: str, int_id: int) -> Optional[Dict[str, Any]]:
        dao = self.get_dao(entity_name)
        data = dao.get_by_id(int_id)
        return data

    def update(self, entity_name: str, int_id: int, data: Dict[str, Any]):
        dao = self.get_dao(entity_name)
        dao.update(int_id, data)

    def delete(self, entity_name: str, int_id: int):
        dao = self.get_dao(entity_name)
        dao.delete(int_id)

    def find_one_by_column(self, entity_name: str, column_name: str, value: Any) -> Optional[Dict[str, Any]]:
        dao = self.get_dao(entity_name)
        data = dao.find_one_by_column(column_name, value)
        return data

    def find_by_column(self, entity_name: str, column_name: str, value: Any) -> List[Dict[str, Any]]:
        dao = self.get_dao(entity_name)
        data_list = dao.find_by_column(column_name, value)
        return data_list

    def get_all(self, entity_name: str) -> List[Dict[str, Any]]:
        dao = self.get_dao(entity_name)
        data_list = dao.get_all()
        return data_list

    # Optional: Provide direct access properties for common DAOs
    @property
    def users(self):
        return self.get_dao("users")

    @property
    def products(self):
        return self.get_dao("products")

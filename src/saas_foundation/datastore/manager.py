from dataclasses import fields, is_dataclass
from datetime import datetime
from types import UnionType
from typing import Any, Dict, List, Optional, Type, Union, get_origin, get_args

from saas_foundation.datastore.dao import BaseDAO
from saas_foundation.datastore.database import execute_query as db_execute_query
from saas_foundation.datastore.schema import create_tables_from_entity_definitions


class DatastoreManager:
    def __init__(
        self,
        logger: Any,
        models: List[Type[Any]] | None = None,
        connection: Any | None = None,
    ):
        self.logger = logger
        self.entity_definitions = {}
        self._daos = {}
        self.connection = connection  # Store the connection

        if models:
            self.register_dataclass_models(models)
            self._initialize_datastore()
        else:
            self._initialize_datastore()

    def _initialize_datastore(self):

        # Create tables based on entity definitions
        create_tables_from_entity_definitions(
            self.entity_definitions, conn=self.connection, logger=self.logger
        )
        # Create DAO instances for each entity
        for entity_name in self.entity_definitions:
            self._daos[entity_name] = BaseDAO(
                entity_name, self.connection, logger=self.logger
            )

    def register_entity_definitions(self, new_entity_definitions):
        """Registers new entity definitions and updates the datastore."""

        # Merge new definitions with existing ones
        self.entity_definitions.update(new_entity_definitions)
        # Create tables for newly registered entities
        create_tables_from_entity_definitions(
            new_entity_definitions, conn=self.connection, logger=self.logger
        )
        # Create DAO instances for newly registered entities
        for entity_name in new_entity_definitions:
            if entity_name not in self._daos:
                self._daos[entity_name] = BaseDAO(
                    entity_name, self.connection, logger=self.logger
                )

    def get_dao(self, entity_name):
        """Returns the DAO instance for a given entity name."""
        if entity_name not in self._daos:
            raise ValueError(f"DAO for entity '{entity_name}' not found.")
        return self._daos[entity_name]

    def _get_column_type(self, python_type: Type) -> str:
        """Maps Python types to SQLite column types."""
        column_type = None

        # Handle Optional types
        if get_origin(python_type) is Union or get_origin(python_type) is UnionType:
            # Extract the actual type from Optional or Union
            args = get_args(python_type)
            python_type = next((arg for arg in args if arg is not type(None)), None)
            if python_type is None:
                raise ValueError(
                    f"Could not determine base type from Optional or Union: {args}"
                )

        # Handle generic types like List and Dict
        if get_origin(python_type) in (list, dict):
            column_type = "TEXT"  # Store lists/dicts as JSON strings
        # Handle Any type
        elif python_type is Any:
            column_type = "TEXT"
        # Ensure python_type is a concrete type before proceeding
        elif not isinstance(python_type, type):
            raise ValueError(f"Resolved type is not a concrete type: {python_type}")
        elif python_type is str:
            column_type = "TEXT"
        elif python_type is int:
            column_type = "INTEGER"
        elif python_type is float:
            column_type = "REAL"
        elif python_type is bool:
            column_type = "INTEGER"  # SQLite stores booleans as 0 or 1
        elif python_type is datetime:
            column_type = "TEXT"  # Store datetime as ISO 8601 string
        else:
            raise ValueError(
                f"Unsupported Python type for schema generation: {python_type}"
            )
        return column_type

    def register_dataclass_models(self, models: List[Type[Any]]):
        """Registers dataclass models and generates entity definitions."""
        new_entity_definitions = {}
        for model in models:
            if not is_dataclass(model):
                raise TypeError(f"Provided object {model.__name__} is not a dataclass.")

            table_name = model.__name__.lower() + "s"  # Simple pluralization
            entity_schema = {}
            for field_info in fields(model):

                if field_info.name == "id":
                    continue  # 'id' is handled implicitly as PRIMARY KEY AUTOINCREMENT

                column_type = self._get_column_type(field_info.type)

                # Add default values for created_at and updated_at
                if field_info.name == "created_at":
                    entity_schema[field_info.name] = (
                        f"{column_type} DEFAULT CURRENT_TIMESTAMP"
                    )
                elif field_info.name == "updated_at":
                    entity_schema[field_info.name] = (
                        f"{column_type} DEFAULT CURRENT_TIMESTAMP"
                    )

                else:
                    entity_schema[field_info.name] = column_type
                    # Add NOT NULL constraint if not Optional and not a default factory
                    is_optional = (
                        get_origin(field_info.type) is Union
                        or get_origin(field_info.type) is Optional
                        or (
                            get_origin(field_info.type) is UnionType
                            and type(None) in get_args(field_info.type)
                        )
                    )

                    if not is_optional:
                        entity_schema[field_info.name] += " NOT NULL"

            new_entity_definitions[table_name] = entity_schema

        self.register_entity_definitions(new_entity_definitions)

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

    def find_one_by_column(
        self, entity_name: str, column_name: str, value: Any
    ) -> Optional[Dict[str, Any]]:
        dao = self.get_dao(entity_name)
        data = dao.find_one_by_column(column_name, value)
        return data

    def find_by_column(
        self, entity_name: str, column_name: str, value: Any
    ) -> List[Dict[str, Any]]:
        dao = self.get_dao(entity_name)
        data_list = dao.find_by_column(column_name, value)
        return data_list

    def get_all(self, entity_name: str) -> List[Dict[str, Any]]:
        dao = self.get_dao(entity_name)
        data_list = dao.get_all()
        return data_list

    def execute_query(self, query: str, params: tuple = ()):  # Add this method
        return db_execute_query(query, params, logger=self.logger)

    # Optional: Provide direct access properties for common DAOs
    @property
    def users(self):
        return self.get_dao("users")

    @property
    def products(self):
        return self.get_dao("products")

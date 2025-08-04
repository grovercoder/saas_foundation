from src.datastore.database import execute_query

def create_tables_from_entity_definitions(entity_definitions):
    """Creates database tables based on provided entity definitions."""
    print("Creating tables from entity definitions...")
    for entity_name, fields in entity_definitions.items():
        columns = []
        for field_name, field_type in fields.items():
            columns.append(f"{field_name} {field_type}")
        
        # Add a primary key if not explicitly defined
        if "id" not in fields:
            columns.insert(0, "id INTEGER PRIMARY KEY AUTOINCREMENT")

        create_table_sql = f"CREATE TABLE IF NOT EXISTS {entity_name} ({', '.join(columns)})"
        try:
            execute_query(create_table_sql)
            print(f"Table '{entity_name}' created or already exists.")
        except Exception as e:
            print(f"Error creating table {entity_name}: {e}")

# Example usage (for testing purposes, will be removed later)
if __name__ == "__main__":
    # This would come from external library discovery
    example_entity_definitions = {
        "users": {
            "name": "TEXT NOT NULL",
            "email": "TEXT UNIQUE NOT NULL"
        },
        "products": {
            "product_name": "TEXT NOT NULL",
            "price": "REAL"
        }
    }
    create_tables_from_entity_definitions(example_entity_definitions)

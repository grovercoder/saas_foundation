from src.datastore.database import execute_query

def create_tables_from_entity_definitions(entity_definitions, conn=None, logger=None):
    """Creates database tables based on provided entity definitions."""
    
    for entity_name, fields in entity_definitions.items():
        columns = []
        for field_name, field_type in fields.items():
            columns.append(f"{field_name} {field_type}")
        
        # Add a primary key if not explicitly defined
        if "id" not in fields:
            columns.insert(0, "id INTEGER PRIMARY KEY AUTOINCREMENT")

        create_table_sql = f"CREATE TABLE IF NOT EXISTS {entity_name} ({', '.join(columns)})"
        execute_query(create_table_sql, conn=conn, logger=logger)
            
        



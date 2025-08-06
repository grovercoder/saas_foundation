from src.datastore.database import execute_query, fetch_one, fetch_all

class BaseDAO:
    def __init__(self, table_name, connection, logger):
        self.table_name = table_name
        self.connection = connection
        self.logger = logger

    def insert(self, data):
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data.values()])
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        cursor = execute_query(query, tuple(data.values()), conn=self.connection, logger=self.logger)
        return cursor.lastrowid

    def get_by_id(self, int_id):
        query = f"SELECT * FROM {self.table_name} WHERE id = ?"
        row = fetch_one(query, (int_id,), conn=self.connection, logger=self.logger)
        if row:
            return dict(row)
        return None

    def get_all(self):
        query = f"SELECT * FROM {self.table_name}"
        rows = fetch_all(query, conn=self.connection, logger=self.logger)
        return [dict(row) for row in rows]

    def update(self, int_id, data):
        set_clauses = ', '.join([f"{key} = ?" for key in data.keys()])
        query = f"UPDATE {self.table_name} SET {set_clauses} WHERE id = ?"
        execute_query(query, tuple(list(data.values()) + [int_id]), conn=self.connection, logger=self.logger)

    def delete(self, int_id):
        query = f"DELETE FROM {self.table_name} WHERE id = ?"
        execute_query(query, (int_id,), conn=self.connection, logger=self.logger)

    def find_one_by_column(self, column_name, value):
        query = f"SELECT * FROM {self.table_name} WHERE {column_name} = ?"
        row = fetch_one(query, (value,), conn=self.connection, logger=self.logger)
        if row:
            return dict(row)
        return None

    def find_by_column(self, column_name, value):
        query = f"SELECT * FROM {self.table_name} WHERE {column_name} = ?"
        rows = fetch_all(query, (value,), conn=self.connection, logger=self.logger)
        return [dict(row) for row in rows]

from src.datastore.database import execute_query, fetch_one, fetch_all
from hashids import Hashids
import os

HASHIDS_SALT = os.getenv("HASHIDS_SALT", "your_default_salt_here") # IMPORTANT: Change this in production
hashids = Hashids(salt=HASHIDS_SALT, min_length=8)

class BaseDAO:
    def __init__(self, table_name):
        self.table_name = table_name

    def _encode_id(self, int_id):
        if int_id is None:
            return None
        return hashids.encode(int_id)

    def _decode_id(self, hash_id):
        if hash_id is None:
            return None
        decoded = hashids.decode(hash_id)
        return decoded[0] if decoded else None

    def insert(self, data):
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data.values()])
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        cursor = execute_query(query, tuple(data.values()))
        return self._encode_id(cursor.lastrowid)

    def get_by_id(self, hash_id):
        int_id = self._decode_id(hash_id)
        if int_id is None:
            return None
        query = f"SELECT * FROM {self.table_name} WHERE id = ?"
        row = fetch_one(query, (int_id,))
        if row:
            # Convert row to dict and encode 'id'
            row_dict = dict(row)
            row_dict['id'] = self._encode_id(row_dict['id'])
            return row_dict
        return None

    def get_all(self):
        query = f"SELECT * FROM {self.table_name}"
        rows = fetch_all(query)
        # Encode 'id' for each row
        encoded_rows = []
        for row in rows:
            row_dict = dict(row)
            row_dict['id'] = self._encode_id(row_dict['id'])
            encoded_rows.append(row_dict)
        return encoded_rows

    def update(self, hash_id, data):
        int_id = self._decode_id(hash_id)
        if int_id is None:
            raise ValueError("Invalid hash ID provided for update.")
        set_clauses = ', '.join([f"{key} = ?" for key in data.keys()])
        query = f"UPDATE {self.table_name} SET {set_clauses} WHERE id = ?"
        execute_query(query, tuple(list(data.values()) + [int_id]))

    def delete(self, hash_id):
        int_id = self._decode_id(hash_id)
        if int_id is None:
            raise ValueError("Invalid hash ID provided for delete.")
        query = f"DELETE FROM {self.table_name} WHERE id = ?"
        execute_query(query, (int_id,))

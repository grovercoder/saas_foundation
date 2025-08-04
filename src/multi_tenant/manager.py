from src.datastore.manager import DatastoreManager
from src.multi_tenant.models import Account, User
import bcrypt
from datetime import datetime, timedelta
import os
import secrets
from src.authorization.manager import AuthorizationManager # Import AuthorizationManager

# Entity definitions for the multi_tenant module
multi_tenant_entity_definitions = {
    "accounts": {
        "name": "TEXT NOT NULL UNIQUE",
        "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP"
    },
    "users": {
        "account_id": "INTEGER NOT NULL",
        "username": "TEXT NOT NULL UNIQUE",
        "password_hash": "TEXT NOT NULL",
        "reset_token": "TEXT",
        "reset_token_created_at": "TEXT",
        "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP",
        "FOREIGN KEY(account_id)": "REFERENCES accounts(id)"
    }
}

# Permissions exposed by the multi_tenant module
MODULE_PERMISSIONS = [
    {"key": "account:create", "name": "Account Create", "description": "Allows creation of new accounts."},
    {"key": "account:read", "name": "Account Read", "description": "Allows reading account details."},
    {"key": "account:update", "name": "Account Update", "description": "Allows updating account details."},
    {"key": "account:delete", "name": "Account Delete", "description": "Allows deletion of accounts."},
    {"key": "user:create", "name": "User Create", "description": "Allows creation of new users within an account."},
    {"key": "user:read", "name": "User Read", "description": "Allows reading user details."},
    {"key": "user:update", "name": "User Update", "description": "Allows updating user details."},
    {"key": "user:delete", "name": "User Delete", "description": "Allows deletion of users."},
    {"key": "user:authenticate", "name": "User Authenticate", "description": "Allows users to authenticate."},
    {"key": "user:reset_password", "name": "User Reset Password", "description": "Allows users to reset their password."},
]

class MultiTenantManager:
    def __init__(self, datastore_manager: DatastoreManager, authorization_manager: AuthorizationManager | None = None):
        self.datastore = datastore_manager
        self.datastore.register_entity_definitions(multi_tenant_entity_definitions)
        self.accounts_dao = self.datastore.get_dao("accounts")
        self.users_dao = self.datastore.get_dao("users")

        if authorization_manager:
            authorization_manager.register_permissions(MODULE_PERMISSIONS)

    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    def _convert_timestamp_to_datetime(self, timestamp_str: str | None) -> datetime | None:
        if timestamp_str:
            try:
                return datetime.fromisoformat(timestamp_str)
            except ValueError:
                # SQLite's CURRENT_TIMESTAMP might not always be ISO format
                # Try a common format if isoformat fails
                try:
                    return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass # Let it return None if neither format works
        return None

    def create_account(self, name: str) -> Account:
        account_id = self.accounts_dao.insert({"name": name})
        # Fetch the newly created account to get the created_at timestamp from the DB
        return self.get_account_by_id(account_id)

    def get_account_by_id(self, account_id: str) -> Account | None:
        account_data = self.accounts_dao.get_by_id(account_id)
        if account_data:
            account_data['created_at'] = self._convert_timestamp_to_datetime(account_data.get('created_at'))
            return Account(**account_data)
        return None

    def create_user(self, account_id: str, username: str, password: str) -> User:
        # Decode account_id for storage in the database
        int_account_id = self.datastore._decode_id(account_id)
        if int_account_id is None:
            raise ValueError("Invalid account ID provided.")

        password_hash = self._hash_password(password)
        user_id = self.users_dao.insert({
            "account_id": int_account_id,
            "username": username,
            "password_hash": password_hash
        })
        return User(id=user_id, account_id=account_id, username=username, password_hash=password_hash)

    def get_user_by_id(self, user_id: str) -> User | None:
        user_data = self.users_dao.get_by_id(user_id)
        if user_data:
            # Encode account_id back to hashid for the User object
            user_data['account_id'] = self.datastore._encode_id(user_data['account_id'])
            user_data['created_at'] = self._convert_timestamp_to_datetime(user_data.get('created_at'))
            user_data['reset_token_created_at'] = self._convert_timestamp_to_datetime(user_data.get('reset_token_created_at'))
            return User(**user_data)
        return None

    def get_user_by_username(self, username: str) -> User | None:
        # This is inefficient for large datasets. A direct query method in BaseDAO would be better.
        # For now, we fetch all and filter.
        all_users = self.users_dao.get_all()
        for user_data in all_users:
            if user_data['username'] == username:
                # Encode account_id back to hashid for the User object
                user_data['account_id'] = self.datastore._encode_id(user_data['account_id'])
                user_data['created_at'] = self._convert_timestamp_to_datetime(user_data.get('created_at'))
                user_data['reset_token_created_at'] = self._convert_timestamp_to_datetime(user_data.get('reset_token_created_at'))
                return User(**user_data)
        return None

    def authenticate_user(self, username: str, password: str) -> User | None:
        user = self.get_user_by_username(username)
        if user and self._verify_password(password, user.password_hash):
            return user
        return None

    def generate_reset_token(self) -> str:
        return secrets.token_urlsafe(32)

    def set_reset_token(self, user_id: str) -> str:
        token = self.generate_reset_token()
        token_created_at = datetime.now().isoformat()
        self.users_dao.update(user_id, {"reset_token": token, "reset_token_created_at": token_created_at})
        return token

    def clear_reset_token(self, user_id: str) -> None:
        self.users_dao.update(user_id, {"reset_token": None, "reset_token_created_at": None})

    def verify_reset_token(self, user_id: str, token: str, expiry_minutes: int = 60) -> bool:
        user = self.get_user_by_id(user_id)
        if not user or user.reset_token != token or not user.reset_token_created_at:
            return False

        token_timestamp = user.reset_token_created_at
        if datetime.now() - token_timestamp > timedelta(minutes=expiry_minutes):
            return False

        return True

    def reset_password(self, user_id: str, new_password: str, token: str) -> bool:
        if self.verify_reset_token(user_id, token):
            hashed_password = self._hash_password(new_password)
            self.users_dao.update(user_id, {"password_hash": hashed_password})
            self.clear_reset_token(user_id)
            return True
        return False

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt

from saas_foundation.authorization.manager import AuthorizationManager
from saas_foundation.datastore.manager import DatastoreManager
from saas_foundation.multi_tenant.models import Account, User

# Entity definitions for the multi_tenant module


# Permissions exposed by the multi_tenant module
MODULE_PERMISSIONS = [
    {
        "key": "account:create",
        "name": "Account Create",
        "description": "Allows creation of new accounts.",
    },
    {
        "key": "account:read",
        "name": "Account Read",
        "description": "Allows reading account details.",
    },
    {
        "key": "account:update",
        "name": "Account Update",
        "description": "Allows updating account details.",
    },
    {
        "key": "account:delete",
        "name": "Account Delete",
        "description": "Allows deletion of accounts.",
    },
    {
        "key": "user:create",
        "name": "User Create",
        "description": "Allows creation of new users within an account.",
    },
    {
        "key": "user:read",
        "name": "User Read",
        "description": "Allows reading user details.",
    },
    {
        "key": "user:update",
        "name": "User Update",
        "description": "Allows updating user details.",
    },
    {
        "key": "user:delete",
        "name": "User Delete",
        "description": "Allows deletion of users.",
    },
    {
        "key": "user:authenticate",
        "name": "User Authenticate",
        "description": "Allows users to authenticate.",
    },
    {
        "key": "user:reset_password",
        "name": "User Reset Password",
        "description": "Allows users to reset their password.",
    },
]


class MultiTenantManager:
    def __init__(
        self,
        logger: Any,
        datastore_manager: DatastoreManager,
        authorization_manager: AuthorizationManager | None = None,
    ):
        self.logger = logger
        self.datastore = datastore_manager
        self.datastore.register_dataclass_models([Account, User])
        self.accounts_dao = self.datastore.get_dao("accounts")
        self.users_dao = self.datastore.get_dao("users")

        if authorization_manager:
            authorization_manager.register_permissions(MODULE_PERMISSIONS)

    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

    def _convert_timestamp_to_datetime(
        self, timestamp_str: str | None
    ) -> datetime | None:
        if timestamp_str:
            try:
                # Attempt to parse as ISO format with timezone
                dt_obj = datetime.fromisoformat(timestamp_str)
                if dt_obj.tzinfo is None:
                    # If no timezone info, assume UTC
                    return dt_obj.replace(tzinfo=timezone.utc)
                return dt_obj
            except ValueError:
                # Fallback for non-ISO formats if necessary, but prefer ISO
                try:
                    return datetime.strptime(
                        timestamp_str, "%Y-%m-%d %H:%M:%S"
                    ).replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
        return None

    def create_account(self, name: str) -> Account:
        account_data = {"name": name}
        account_id = self.datastore.insert("accounts", account_data)
        retrieved_account_data = self.datastore.get_by_id("accounts", account_id)
        if retrieved_account_data:
            retrieved_account_data["created_at"] = self._convert_timestamp_to_datetime(
                retrieved_account_data.get("created_at")
            )
            return Account(**retrieved_account_data)
        self.logger.error("Failed to create account.")
        raise ValueError("Failed to create account.")

    def get_account_by_id(self, account_id: int) -> Account | None:
        account_data = self.datastore.get_by_id("accounts", account_id)
        if account_data:
            account_data["created_at"] = self._convert_timestamp_to_datetime(
                account_data.get("created_at")
            )
            return Account(
                id=account_data["id"],
                name=account_data["name"],
                created_at=account_data.get("created_at"),
            )
        return None

    def create_user(self, account_id: int, username: str, password: str) -> User:
        if not self.datastore.get_by_id("accounts", account_id):
            self.logger.error(f"Invalid account ID provided: {account_id}")
            raise ValueError("Invalid account ID provided.")

        hashed_password = self._hash_password(password)
        user_data = {
            "account_id": account_id,
            "username": username,
            "password_hash": hashed_password,
        }
        user_id = self.datastore.insert("users", user_data)
        retrieved_user_data = self.datastore.get_by_id("users", user_id)
        if retrieved_user_data:
            retrieved_user_data["created_at"] = self._convert_timestamp_to_datetime(
                retrieved_user_data.get("created_at")
            )
            retrieved_user_data["reset_token_created_at"] = (
                self._convert_timestamp_to_datetime(
                    retrieved_user_data.get("reset_token_created_at")
                )
            )
            return User(**retrieved_user_data)
        self.logger.error("Failed to create user.")
        raise ValueError("Failed to create user.")

    def authenticate_user(self, username: str, password: str) -> User | None:
        user_data = self.datastore.find_one_by_column("users", "username", username)
        if user_data and self._verify_password(password, user_data["password_hash"]):
            user_data["created_at"] = self._convert_timestamp_to_datetime(
                user_data.get("created_at")
            )
            user_data["reset_token_created_at"] = self._convert_timestamp_to_datetime(
                user_data.get("reset_token_created_at")
            )
            return User(**user_data)
        return None

    def generate_reset_token(self, username: str) -> str | None:
        user_data = self.datastore.find_one_by_column("users", "username", username)
        if user_data:
            token = secrets.token_urlsafe(32)
            token_created_at = datetime.now(timezone.utc)
            self.datastore.update(
                "users",
                user_data["id"],
                {
                    "reset_token": token,
                    "reset_token_created_at": token_created_at.isoformat(),
                },
            )
            return token
        return None

    def reset_password(self, username: str, token: str, new_password: str) -> bool:
        user_data = self.datastore.find_one_by_column("users", "username", username)
        if user_data and user_data.get("reset_token") == token:
            token_created_at = self._convert_timestamp_to_datetime(
                user_data.get("reset_token_created_at")
            )
            if token_created_at and datetime.now(
                timezone.utc
            ) - token_created_at < timedelta(hours=1):
                hashed_password = self._hash_password(new_password)
                self.datastore.update(
                    "users",
                    user_data["id"],
                    {
                        "password_hash": hashed_password,
                        "reset_token": None,
                        "reset_token_created_at": None,
                    },
                )
                return True
        return False

    def get_user_by_username(self, username: str) -> User | None:
        user_data = self.datastore.find_one_by_column("users", "username", username)
        if user_data:
            user_data["created_at"] = self._convert_timestamp_to_datetime(
                user_data.get("created_at")
            )
            user_data["reset_token_created_at"] = self._convert_timestamp_to_datetime(
                user_data.get("reset_token_created_at")
            )
            return User(**user_data)
        return None

    def get_user_by_id(self, user_id: int) -> User | None:
        user_data = self.datastore.get_by_id("users", user_id)
        if user_data:
            user_data["created_at"] = self._convert_timestamp_to_datetime(
                user_data.get("created_at")
            )
            user_data["reset_token_created_at"] = self._convert_timestamp_to_datetime(
                user_data.get("reset_token_created_at")
            )
            return User(**user_data)
        return None

    def update_user(self, user_id: int, data: dict) -> bool:
        user = self.get_user_by_id(user_id)
        if not user:
            self.logger.error(f"User with ID {user_id} not found for update.")
            return False

        if "password" in data:
            data["password_hash"] = self._hash_password(data["password"])
            del data["password"]

        self.datastore.update("users", user_id, data)
        return True

    def delete_user(self, user_id: int) -> bool:
        user = self.get_user_by_id(user_id)
        if not user:
            self.logger.error(f"User with ID {user_id} not found for deletion.")
            return False
        self.datastore.delete("users", user_id)
        return True

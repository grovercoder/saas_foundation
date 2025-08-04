from src.datastore.manager import DatastoreManager
from src.authorization.manager import AuthorizationManager
from src.payment_gateway.manager import PaymentGatewayManager
from src.multi_tenant.manager import MultiTenantManager # Added import for MultiTenantManager
from src.subscription.models import Limit, Feature, Tier, Subscription
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import json # For storing features and limits as JSON strings
import secrets # For generating secure tokens

# Entity definitions for the subscription module
subscription_entity_definitions = {
    "limits": {
        "key": "TEXT NOT NULL UNIQUE",
        "name": "TEXT NOT NULL",
        "description": "TEXT",
        "default_value": "TEXT" # Stored as JSON string
    },
    "features": {
        "key": "TEXT NOT NULL UNIQUE",
        "name": "TEXT NOT NULL",
        "description": "TEXT",
        "permissions": "TEXT" # Stored as JSON string (list of permission keys)
    },
    "tiers": {
        "key": "TEXT NOT NULL UNIQUE",
        "status": "TEXT NOT NULL",
        "name": "TEXT NOT NULL",
        "description": "TEXT",
        "monthly_cost": "REAL NOT NULL",
        "yearly_cost": "REAL NOT NULL",
        "stripe_product_id": "TEXT",
        "features": "TEXT", # Stored as JSON string (list of feature keys)
        "limits": "TEXT", # Stored as JSON string (dict of limit_key: value)
        "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "TEXT DEFAULT CURRENT_TIMESTAMP"
    },
    "subscriptions": {
        "account_id": "INTEGER NOT NULL",
        "tier_id": "INTEGER NOT NULL",
        "stripe_subscription_id": "TEXT NOT NULL UNIQUE",
        "status": "TEXT NOT NULL",
        "current_period_start": "TEXT NOT NULL",
        "current_period_end": "TEXT NOT NULL",
        "cancel_at_period_end": "INTEGER NOT NULL", # SQLite stores booleans as 0 or 1
        "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "TEXT DEFAULT CURRENT_TIMESTAMP",
        "FOREIGN KEY(account_id)": "REFERENCES accounts(id)",
        "FOREIGN KEY(tier_id)": "REFERENCES tiers(id)"
    }
}

# Permissions exposed by the subscription module
MODULE_PERMISSIONS = [
    {"key": "limit:create", "name": "Limit Create", "description": "Allows creation of new limits."},
    {"key": "limit:read", "name": "Limit Read", "description": "Allows reading limit details."},
    {"key": "limit:update", "name": "Limit Update", "description": "Allows updating limit details."},
    {"key": "limit:delete", "name": "Limit Delete", "description": "Allows deletion of limits."},
    {"key": "feature:create", "name": "Feature Create", "description": "Allows creation of new features."},
    {"key": "feature:read", "name": "Feature Read", "description": "Allows reading feature details."},
    {"key": "feature:update", "name": "Feature Update", "description": "Allows updating feature details."},
    {"key": "feature:delete", "name": "Feature Delete", "description": "Allows deletion of features."},
    {"key": "tier:create", "name": "Tier Create", "description": "Allows creation of new tiers."},
    {"key": "tier:read", "name": "Tier Read", "description": "Allows reading tier details."},
    {"key": "tier:update", "name": "Tier Update", "description": "Allows updating tier details."},
    {"key": "tier:delete", "name": "Tier Delete", "description": "Allows deletion of tiers."},
    {"key": "tier:activate", "name": "Tier Activate", "description": "Allows activating tiers."},
    {"key": "tier:deactivate", "name": "Tier Deactivate", "description": "Allows deactivating tiers."},
]

class SubscriptionManager:
    def __init__(
        self,
        datastore_manager: DatastoreManager,
        payment_gateway_manager: PaymentGatewayManager,
        authorization_manager: AuthorizationManager | None = None,
        multi_tenant_manager: MultiTenantManager | None = None
    ):

        self.datastore = datastore_manager
        self.payment_gateway = payment_gateway_manager
        self.multi_tenant_manager = multi_tenant_manager # Store multi_tenant_manager
        self.datastore.register_entity_definitions(subscription_entity_definitions)
        self.limits_dao = self.datastore.get_dao("limits")
        self.features_dao = self.datastore.get_dao("features")
        self.tiers_dao = self.datastore.get_dao("tiers")
        self.subscriptions_dao = self.datastore.get_dao("subscriptions")

        if authorization_manager:
            authorization_manager.register_permissions(MODULE_PERMISSIONS)

    def _convert_timestamp_to_datetime(self, timestamp_str: str | None) -> datetime | None:
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
                    return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
        return None

    def _convert_datetime_to_isoformat(self, dt_obj: datetime) -> str:
        return dt_obj.isoformat()

    # --- Tier/Feature/Limit Management ---
    def create_limit(self, key: str, name: str, description: str, default_value: Any) -> Limit:
        limit_id = self.limits_dao.insert({
            "key": key,
            "name": name,
            "description": description,
            "default_value": json.dumps(default_value)
        })
        return self.get_limit_by_id(limit_id)

    def get_limit_by_id(self, limit_id: str) -> Limit | None:
        limit_data = self.limits_dao.get_by_id(limit_id)
        if limit_data:
            limit_data['default_value'] = json.loads(limit_data['default_value'])
            return Limit(**limit_data)
        return None

    def get_limit_by_key(self, key: str) -> Limit | None:
        limit_data = self.limits_dao.find_one_by_column("key", key)
        if limit_data:
            limit_data['default_value'] = json.loads(limit_data['default_value'])
            return Limit(**limit_data)
        return None

    def create_feature(self, key: str, name: str, description: str, permissions: List[str]) -> Feature:
        feature_id = self.features_dao.insert({
            "key": key,
            "name": name,
            "description": description,
            "permissions": json.dumps(permissions)
        })
        return self.get_feature_by_id(feature_id)

    def get_feature_by_id(self, feature_id: str) -> Feature | None:
        feature_data = self.features_dao.get_by_id(feature_id)
        if feature_data:
            feature_data['permissions'] = json.loads(feature_data['permissions'])
            return Feature(**feature_data)
        return None

    def get_feature_by_key(self, key: str) -> Feature | None:
        feature_data = self.features_dao.find_one_by_column("key", key)
        if feature_data:
            feature_data['permissions'] = json.loads(feature_data['permissions'])
            return Feature(**feature_data)
        return None

    def create_tier(
        self,
        key: str,
        name: str,
        description: str,
        monthly_cost: float,
        yearly_cost: float,
        status: str = "draft",
        features: List[str] = None,
        limits: Dict[str, Any] = None,
        stripe_product_id: str = None
    ) -> Tier:
        if features is None:
            features = []
        if limits is None:
            limits = {}

        # Create Stripe Product if stripe_product_id is not provided
        if not stripe_product_id:
            product = self.payment_gateway.stripe.create_product(name, description)
            stripe_product_id = product['id']

        tier_id = self.tiers_dao.insert({
            "key": key,
            "status": status,
            "name": name,
            "description": description,
            "monthly_cost": monthly_cost,
            "yearly_cost": yearly_cost,
            "stripe_product_id": stripe_product_id,
            "features": json.dumps(features),
            "limits": json.dumps(limits)
        })
        return self.get_tier_by_id(tier_id)

    def get_tier_by_id(self, tier_id: str) -> Tier | None:
        tier_data = self.tiers_dao.get_by_id(tier_id)
        if tier_data:
            tier_data['features'] = json.loads(tier_data['features'])
            tier_data['limits'] = json.loads(tier_data['limits'])
            tier_data['created_at'] = self._convert_timestamp_to_datetime(tier_data.get('created_at'))
            tier_data['updated_at'] = self._convert_timestamp_to_datetime(tier_data.get('updated_at'))
            return Tier(**tier_data)
        return None

    def get_tier_by_key(self, key: str) -> Tier | None:
        tier_data = self.tiers_dao.find_one_by_column("key", key)
        if tier_data:
            tier_data['features'] = json.loads(tier_data['features'])
            tier_data['limits'] = json.loads(tier_data['limits'])
            tier_data['created_at'] = self._convert_timestamp_to_datetime(tier_data.get('created_at'))
            tier_data['updated_at'] = self._convert_timestamp_to_datetime(tier_data.get('updated_at'))
            return Tier(**tier_data)
        return None

    def update_tier(self, tier_id: str, **kwargs) -> Tier | None:
        update_data = {}
        if "features" in kwargs:
            update_data["features"] = json.dumps(kwargs["features"])
        if "limits" in kwargs:
            update_data["limits"] = json.dumps(kwargs["limits"])

        for key, value in kwargs.items():
            if key not in ["features", "limits"]:
                update_data[key] = value
        
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.tiers_dao.update(tier_id, update_data)
        return self.get_tier_by_id(tier_id)

    def deactivate_tier(self, tier_id: str) -> Tier | None:
        # Check if there are any active subscriptions for this tier
        active_subscriptions = self.subscriptions_dao.find_by_column("tier_id", self.datastore._decode_id(tier_id))
        if active_subscriptions:
            raise ValueError("Cannot deactivate tier with active subscriptions.")
        return self.update_tier(tier_id, status="deactivated")

    def activate_tier(self, tier_id: str, status: str = "active:public") -> Tier | None:
        return self.update_tier(tier_id, status=status)

    def delete_tier(self, tier_id: str):
        tier = self.get_tier_by_id(tier_id)
        if not tier:
            raise ValueError(f"Tier with ID {tier_id} not found.")
        if tier.status != "deactivated":
            raise ValueError(f"Tier with ID {tier_id} must be deactivated before deletion.")
        self.tiers_dao.delete(tier_id)

    # --- Subscription Management ---
    def create_subscription(
        self,
        account_id: str,
        tier_id: str,
        stripe_subscription_id: str,
        status: str,
        current_period_start: datetime,
        current_period_end: datetime,
        cancel_at_period_end: bool
    ) -> Subscription:
        int_account_id = self.datastore._decode_id(account_id)
        if int_account_id is None:
            raise ValueError("Invalid account ID provided.")

        int_tier_id = self.datastore._decode_id(tier_id)
        if int_tier_id is None:
            raise ValueError("Invalid tier ID provided.")

        subscription_id = self.subscriptions_dao.insert({
            "account_id": int_account_id,
            "tier_id": int_tier_id,
            "stripe_subscription_id": stripe_subscription_id,
            "status": status,
            "current_period_start": self._convert_datetime_to_isoformat(current_period_start),
            "current_period_end": self._convert_datetime_to_isoformat(current_period_end),
            "cancel_at_period_end": 1 if cancel_at_period_end else 0
        })
        return self.get_subscription_by_id(subscription_id)

    def get_subscription_by_id(self, subscription_id: str) -> Subscription | None:
        sub_data = self.subscriptions_dao.get_by_id(subscription_id)
        if sub_data:
            sub_data['account_id'] = self.datastore._encode_id(sub_data['account_id'])
            sub_data['tier_id'] = self.datastore._encode_id(sub_data['tier_id'])
            sub_data['current_period_start'] = self._convert_timestamp_to_datetime(sub_data['current_period_start'])
            sub_data['current_period_end'] = self._convert_timestamp_to_datetime(sub_data['current_period_end'])
            sub_data['created_at'] = self._convert_timestamp_to_datetime(sub_data.get('created_at'))
            sub_data['updated_at'] = self._convert_timestamp_to_datetime(sub_data.get('updated_at'))
            sub_data['cancel_at_period_end'] = bool(sub_data['cancel_at_period_end'])
            return Subscription(**sub_data)
        return None

    def get_subscription_by_stripe_id(self, stripe_subscription_id: str) -> Subscription | None:
        all_subs = self.subscriptions_dao.get_all()
        for sub_data in all_subs:
            if sub_data['stripe_subscription_id'] == stripe_subscription_id:
                sub_data['account_id'] = self.datastore._encode_id(sub_data['account_id'])
                sub_data['tier_id'] = self.datastore._encode_id(sub_data['tier_id'])
                sub_data['current_period_start'] = self._convert_timestamp_to_datetime(sub_data['current_period_start'])
                sub_data['current_period_end'] = self._convert_timestamp_to_datetime(sub_data['current_period_end'])
                sub_data['created_at'] = self._convert_timestamp_to_datetime(sub_data.get('created_at'))
                sub_data['updated_at'] = self._convert_timestamp_to_datetime(sub_data.get('updated_at'))
                sub_data['cancel_at_period_end'] = bool(sub_data['cancel_at_period_end'])
                return Subscription(**sub_data)
        return None

    def update_subscription(self, subscription_id: str, **kwargs) -> Subscription | None:
        update_data = {}
        if "current_period_start" in kwargs:
            update_data["current_period_start"] = self._convert_datetime_to_isoformat(kwargs["current_period_start"])
        if "current_period_end" in kwargs:
            update_data["current_period_end"] = self._convert_datetime_to_isoformat(kwargs["current_period_end"])
        if "cancel_at_period_end" in kwargs:
            update_data["cancel_at_period_end"] = 1 if kwargs["cancel_at_period_end"] else 0

        for key, value in kwargs.items():
            if key not in ["current_period_start", "current_period_end", "cancel_at_period_end"]:
                update_data[key] = value
        
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.subscriptions_dao.update(subscription_id, update_data)
        return self.get_subscription_by_id(subscription_id)

    def handle_stripe_webhook(self, event_payload: dict) -> dict | None:
        event_type = event_payload.get('type')

        if event_type == 'checkout.session.completed':
            session = event_payload['data']['object']
            customer_id = session['customer']
            subscription_id = session['subscription']
            # Assuming you store tier_id in metadata or can derive it
            # For now, let's assume tier_id is passed in client_reference_id or similar
            # Or, we fetch the subscription from Stripe to get the price/product ID

            # Fetch subscription from Stripe to get details
            stripe_subscription = self.payment_gateway.stripe.get_subscription(subscription_id) # Assuming this method exists
            if not stripe_subscription:
                print(f"Error: Stripe subscription {subscription_id} not found.")
                return None

            # Get tier based on Stripe product ID
            stripe_product_id = stripe_subscription['items']['data'][0]['price']['product']
            tier = None
            all_tiers = self.tiers_dao.get_all()
            for t_data in all_tiers:
                if t_data['stripe_product_id'] == stripe_product_id:
                    tier = self.get_tier_by_id(t_data['id'])
                    break
            
            if not tier:
                print(f"Debug: Stripe product ID from webhook: {stripe_product_id}")
                all_tiers_debug = self.tiers_dao.get_all()
                for t_data_debug in all_tiers_debug:
                    print(f"Debug: Tier in DB: {t_data_debug.get('key')}, Stripe Product ID: {t_data_debug.get('stripe_product_id')}")
                print(f"Error: Tier not found for Stripe product ID {stripe_product_id}.")
                return None

            # Create account and user if they don't exist
            # For simplicity, let's assume customer_id is linked to an account in our system
            # Or, create a new account and user for this subscription
            # For now, let's create a new account and user
            account_name = f"Stripe Customer {customer_id}"
            account = self.multi_tenant_manager.create_account(account_name) # Assuming multi_tenant_manager is available
            user = self.multi_tenant_manager.create_user(account.id, f"user_{customer_id}", secrets.token_urlsafe(16))

            # Create subscription record
            subscription = self.create_subscription(
                account.id,
                tier.id,
                stripe_subscription['id'],
                stripe_subscription['status'],
                datetime.fromtimestamp(stripe_subscription['current_period_start'], tz=timezone.utc),
                datetime.fromtimestamp(stripe_subscription['current_period_end'], tz=timezone.utc),
                stripe_subscription['cancel_at_period_end']
            )
            print(f"Subscription created for account {account.id} and tier {tier.key}.")
            return subscription # Return the Subscription object

        # Add other webhook event types here (e.g., invoice.payment_succeeded, customer.subscription.updated)
        return None

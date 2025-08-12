import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from saas_foundation.authorization.manager import AuthorizationManager
from saas_foundation.datastore.manager import DatastoreManager
from saas_foundation.multi_tenant.manager import MultiTenantManager
from saas_foundation.payment_gateway.manager import PaymentGatewayManager
from saas_foundation.subscription.models import Feature, Limit, Subscription, Tier

# Entity definitions for the subscription module


# Permissions exposed by the subscription module
MODULE_PERMISSIONS = [
    {
        "key": "limit:create",
        "name": "Limit Create",
        "description": "Allows creation of new limits.",
    },
    {
        "key": "limit:read",
        "name": "Limit Read",
        "description": "Allows reading limit details.",
    },
    {
        "key": "limit:update",
        "name": "Limit Update",
        "description": "Allows updating limit details.",
    },
    {
        "key": "limit:delete",
        "name": "Limit Delete",
        "description": "Allows deletion of limits.",
    },
    {
        "key": "feature:create",
        "name": "Feature Create",
        "description": "Allows creation of new features.",
    },
    {
        "key": "feature:read",
        "name": "Feature Read",
        "description": "Allows reading feature details.",
    },
    {
        "key": "feature:update",
        "name": "Feature Update",
        "description": "Allows updating feature details.",
    },
    {
        "key": "feature:delete",
        "name": "Feature Delete",
        "description": "Allows deletion of features.",
    },
    {
        "key": "tier:create",
        "name": "Tier Create",
        "description": "Allows creation of new tiers.",
    },
    {
        "key": "tier:read",
        "name": "Tier Read",
        "description": "Allows reading tier details.",
    },
    {
        "key": "tier:update",
        "name": "Tier Update",
        "description": "Allows updating tier details.",
    },
    {
        "key": "tier:delete",
        "name": "Tier Delete",
        "description": "Allows deletion of tiers.",
    },
    {
        "key": "tier:activate",
        "name": "Tier Activate",
        "description": "Allows activating tiers.",
    },
    {
        "key": "tier:deactivate",
        "name": "Tier Deactivate",
        "description": "Allows deactivating tiers.",
    },
]


class SubscriptionManager:
    def __init__(
        self,
        logger: Any,
        datastore_manager: DatastoreManager,
        payment_gateway_manager: PaymentGatewayManager,
        authorization_manager: AuthorizationManager | None = None,
        multi_tenant_manager: MultiTenantManager | None = None,
    ):

        self.logger = logger
        self.datastore = datastore_manager
        self.payment_gateway = payment_gateway_manager
        self.multi_tenant_manager = multi_tenant_manager  # Store multi_tenant_manager
        self.datastore.register_dataclass_models([Limit, Feature, Tier, Subscription])
        self.limits_dao = self.datastore.get_dao("limits")
        self.features_dao = self.datastore.get_dao("features")
        self.tiers_dao = self.datastore.get_dao("tiers")
        self.subscriptions_dao = self.datastore.get_dao("subscriptions")

        if authorization_manager:
            authorization_manager.register_permissions(MODULE_PERMISSIONS)

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

    def _convert_datetime_to_isoformat(self, dt_obj: datetime) -> str:
        return dt_obj.isoformat()

    # --- Tier/Feature/Limit Management ---
    def create_limit(
        self, key: str, name: str, description: str, default_value: Any
    ) -> Limit:
        limit_data = {
            "key": key,
            "name": name,
            "description": description,
            "default_value": json.dumps(default_value),
        }
        hash_id = self.datastore.insert("limits", limit_data)
        return self.get_limit_by_id(hash_id)

    def get_limit_by_id(self, limit_id: str) -> Limit | None:
        limit_data = self.datastore.get_by_id("limits", limit_id)
        if limit_data:
            limit_data["default_value"] = json.loads(limit_data["default_value"])
            return Limit(**limit_data)
        return None

    def get_limit_by_key(self, key: str) -> Limit | None:
        limit_data = self.datastore.find_one_by_column("limits", "key", key)
        if limit_data:
            limit_data["default_value"] = json.loads(limit_data["default_value"])
            return Limit(**limit_data)
        return None

    def create_feature(
        self, key: str, name: str, description: str, permissions: List[str]
    ) -> Feature:
        feature_data = {
            "key": key,
            "name": name,
            "description": description,
            "permissions": json.dumps(permissions),
        }
        hash_id = self.datastore.insert("features", feature_data)
        return self.get_feature_by_id(hash_id)

    def get_feature_by_id(self, feature_id: str) -> Feature | None:
        feature_data = self.datastore.get_by_id("features", feature_id)
        if feature_data:
            feature_data["permissions"] = json.loads(feature_data["permissions"])
            return Feature(**feature_data)
        return None

    def get_feature_by_key(self, key: str) -> Feature | None:
        feature_data = self.datastore.find_one_by_column("features", "key", key)
        if feature_data:
            feature_data["permissions"] = json.loads(feature_data["permissions"])
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
        stripe_product_id: str = None,
    ) -> Tier:
        if features is None:
            features = []
        if limits is None:
            limits = {}

        # Create Stripe Product if stripe_product_id is not provided
        if not stripe_product_id:
            product = self.payment_gateway.stripe.create_product(name, description)
            stripe_product_id = product["id"]

        # Create Stripe Product if stripe_product_id is not provided
        if not stripe_product_id:
            product = self.payment_gateway.stripe.create_product(name, description)
            stripe_product_id = product["id"]

        # Create Stripe Prices
        # Assuming currency is 'usd' for now, this should be configurable
        currency = "usd"

        monthly_price_id = None
        if monthly_cost is not None:
            monthly_price = self.payment_gateway.stripe.create_price(
                product_id=stripe_product_id,
                unit_amount=monthly_cost,
                currency=currency,
                recurring_interval="month",
                nickname=f"{name} Monthly",
            )
            monthly_price_id = monthly_price["id"]

        yearly_price_id = None
        if yearly_cost is not None:
            yearly_price = self.payment_gateway.stripe.create_price(
                product_id=stripe_product_id,
                unit_amount=yearly_cost,
                currency=currency,
                recurring_interval="year",
                nickname=f"{name} Yearly",
            )
            yearly_price_id = yearly_price["id"]

        hash_id = self.datastore.insert(
            "tiers",
            {
                "key": key,
                "status": status,
                "name": name,
                "description": description,
                "monthly_cost": monthly_cost,
                "yearly_cost": yearly_cost,
                "stripe_product_id": stripe_product_id,
                "monthly_price_id": monthly_price_id,
                "yearly_price_id": yearly_price_id,
                "features": json.dumps(features),
                "limits": json.dumps(limits),
            },
        )
        return self.get_tier_by_id(hash_id)

    def get_tier_by_id(self, tier_id: str) -> Tier | None:
        tier_data = self.datastore.get_by_id("tiers", tier_id)
        if tier_data:
            tier_data["features"] = json.loads(tier_data["features"])
            tier_data["limits"] = json.loads(tier_data["limits"])
            tier_data["created_at"] = self._convert_timestamp_to_datetime(
                tier_data.get("created_at")
            )
            tier_data["updated_at"] = self._convert_timestamp_to_datetime(
                tier_data.get("updated_at")
            )
            tier_data["monthly_price_id"] = tier_data.get("monthly_price_id")
            tier_data["yearly_price_id"] = tier_data.get("yearly_price_id")
            return Tier(**tier_data)
        return None

    def get_tier_by_key(self, key: str) -> Tier | None:
        tier_data = self.datastore.find_one_by_column("tiers", "key", key)
        if tier_data:
            tier_data["features"] = json.loads(tier_data["features"])
            tier_data["limits"] = json.loads(tier_data["limits"])
            tier_data["created_at"] = self._convert_timestamp_to_datetime(
                tier_data.get("created_at")
            )
            tier_data["updated_at"] = self._convert_timestamp_to_datetime(
                tier_data.get("updated_at")
            )
            tier_data["monthly_price_id"] = tier_data.get("monthly_price_id")
            tier_data["yearly_price_id"] = tier_data.get("yearly_price_id")
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
        self.datastore.update("tiers", tier_id, update_data)
        return self.get_tier_by_id(tier_id)

    def deactivate_tier(self, tier_id: str) -> Tier | None:
        # Check if there are any active subscriptions for this tier
        # Need to get all subscriptions and filter by tier_id (hash_id)
        all_subscriptions = self.datastore.get_all("subscriptions")
        active_subscriptions = [
            sub
            for sub in all_subscriptions
            if sub.get("tier_id") == tier_id and sub.get("status") == "active"
        ]

        if active_subscriptions:
            self.logger.error("Cannot deactivate tier with active subscriptions.")
            raise ValueError("Cannot deactivate tier with active subscriptions.")
        return self.update_tier(tier_id, status="deactivated")

    def activate_tier(self, tier_id: str, status: str = "active:public") -> Tier | None:
        return self.update_tier(tier_id, status=status)

    def delete_tier(self, tier_id: str):
        tier = self.get_tier_by_id(tier_id)
        if not tier:
            self.logger.error(f"Tier with ID {tier_id} not found.")
            raise ValueError(f"Tier with ID {tier_id} not found.")
        if tier.status != "deactivated":
            self.logger.error(
                f"Tier with ID {tier_id} must be deactivated before deletion. Current status: {tier.status}"
            )
            raise ValueError(
                f"Tier with ID {tier_id} must be deactivated before deletion."
            )

        # Archive corresponding Stripe product if it exists
        if tier.stripe_product_id:
            try:
                self.payment_gateway.stripe.archive_product(tier.stripe_product_id)
                self.logger.info(
                    f"Archived Stripe product {tier.stripe_product_id} for tier {tier_id}."
                )
            except Exception as e:
                self.logger.error(
                    f"Failed to archive Stripe product {tier.stripe_product_id} for tier {tier_id}: {e}"
                )
                # Do not re-raise, allow local tier deletion to proceed

        self.datastore.delete("tiers", tier_id)

    def get_all_limits(self) -> List[Limit]:
        all_limits_data = self.datastore.get_all("limits")
        return [
            Limit(
                **{
                    **limit_data,
                    "default_value": json.loads(limit_data["default_value"]),
                }
            )
            for limit_data in all_limits_data
        ]

    def get_all_features(self) -> List[Feature]:
        all_features_data = self.datastore.get_all("features")
        return [
            Feature(
                **{
                    **feature_data,
                    "permissions": json.loads(feature_data["permissions"]),
                }
            )
            for feature_data in all_features_data
        ]

    def get_all_tiers(self) -> List[Tier]:
        all_tiers_data = self.datastore.get_all("tiers")
        tiers = []
        for tier_data in all_tiers_data:
            tier_data["features"] = json.loads(tier_data["features"])
            tier_data["limits"] = json.loads(tier_data["limits"])
            tier_data["created_at"] = self._convert_timestamp_to_datetime(
                tier_data.get("created_at")
            )
            tier_data["updated_at"] = self._convert_timestamp_to_datetime(
                tier_data.get("updated_at")
            )
            tier_data["monthly_price_id"] = tier_data.get("monthly_price_id")
            tier_data["yearly_price_id"] = tier_data.get("yearly_price_id")
            tiers.append(Tier(**tier_data))
        return tiers

    def get_all_subscriptions(self) -> List[Subscription]:
        all_subscriptions_data = self.datastore.get_all("subscriptions")
        subscriptions = []
        for sub_data in all_subscriptions_data:
            sub_data["current_period_start"] = self._convert_timestamp_to_datetime(
                sub_data["current_period_start"]
            )
            sub_data["current_period_end"] = self._convert_timestamp_to_datetime(
                sub_data["current_period_end"]
            )
            sub_data["created_at"] = self._convert_timestamp_to_datetime(
                sub_data.get("created_at")
            )
            sub_data["updated_at"] = self._convert_timestamp_to_datetime(
                sub_data.get("updated_at")
            )
            sub_data["cancel_at_period_end"] = bool(sub_data["cancel_at_period_end"])
            subscriptions.append(
                Subscription(
                    id=sub_data["id"],
                    account_id=sub_data["account_id"],
                    tier_id=sub_data["tier_id"],
                    stripe_subscription_id=sub_data["stripe_subscription_id"],
                    status=sub_data["status"],
                    current_period_start=sub_data["current_period_start"],
                    current_period_end=sub_data["current_period_end"],
                    cancel_at_period_end=sub_data["cancel_at_period_end"],
                    created_at=sub_data["created_at"],
                    updated_at=sub_data["updated_at"],
                )
            )
        return subscriptions

    # --- Subscription Management ---
    def create_subscription(
        self,
        account_id: str,
        tier_id: str,
        stripe_subscription_id: str,
        status: str,
        current_period_start: datetime,
        current_period_end: datetime,
        cancel_at_period_end: bool,
    ) -> Subscription:
        subscription_data = {
            "account_id": int(account_id),
            "tier_id": int(tier_id),
            "stripe_subscription_id": stripe_subscription_id,
            "status": status,
            "current_period_start": self._convert_datetime_to_isoformat(
                current_period_start
            ),
            "current_period_end": self._convert_datetime_to_isoformat(
                current_period_end
            ),
            "cancel_at_period_end": 1 if cancel_at_period_end else 0,
        }
        hash_id = self.datastore.insert("subscriptions", subscription_data)
        return self.get_subscription_by_id(hash_id)

    def get_subscription_by_id(self, subscription_id: int) -> Subscription | None:
        sub_data = self.datastore.get_by_id("subscriptions", subscription_id)
        if sub_data:
            sub_data["current_period_start"] = self._convert_timestamp_to_datetime(
                sub_data["current_period_start"]
            )
            sub_data["current_period_end"] = self._convert_timestamp_to_datetime(
                sub_data["current_period_end"]
            )
            sub_data["created_at"] = self._convert_timestamp_to_datetime(
                sub_data.get("created_at")
            )
            sub_data["updated_at"] = self._convert_timestamp_to_datetime(
                sub_data.get("updated_at")
            )
            sub_data["cancel_at_period_end"] = bool(sub_data["cancel_at_period_end"])
            return Subscription(
                id=sub_data["id"],
                account_id=sub_data["account_id"],
                tier_id=sub_data["tier_id"],
                stripe_subscription_id=sub_data["stripe_subscription_id"],
                status=sub_data["status"],
                current_period_start=sub_data["current_period_start"],
                current_period_end=sub_data["current_period_end"],
                cancel_at_period_end=sub_data["cancel_at_period_end"],
                created_at=sub_data["created_at"],
                updated_at=sub_data["updated_at"],
            )
        return None

    def get_subscription_by_stripe_id(
        self, stripe_subscription_id: str
    ) -> Subscription | None:
        sub_data = self.datastore.find_one_by_column(
            "subscriptions", "stripe_subscription_id", stripe_subscription_id
        )
        if sub_data:
            sub_data["current_period_start"] = self._convert_timestamp_to_datetime(
                sub_data["current_period_start"]
            )
            sub_data["current_period_end"] = self._convert_timestamp_to_datetime(
                sub_data["current_period_end"]
            )
            sub_data["created_at"] = self._convert_timestamp_to_datetime(
                sub_data.get("created_at")
            )
            sub_data["updated_at"] = self._convert_timestamp_to_datetime(
                sub_data.get("updated_at")
            )
            sub_data["cancel_at_period_end"] = bool(sub_data["cancel_at_period_end"])
            return Subscription(
                id=sub_data["id"],
                account_id=sub_data["account_id"],
                tier_id=sub_data["tier_id"],
                stripe_subscription_id=sub_data["stripe_subscription_id"],
                status=sub_data["status"],
                current_period_start=sub_data["current_period_start"],
                current_period_end=sub_data["current_period_end"],
                cancel_at_period_end=sub_data["cancel_at_period_end"],
                created_at=sub_data["created_at"],
                updated_at=sub_data["updated_at"],
            )
        return None

    def update_subscription(
        self, subscription_id: str, **kwargs
    ) -> Subscription | None:
        update_data = {}
        if "current_period_start" in kwargs:
            update_data["current_period_start"] = self._convert_datetime_to_isoformat(
                kwargs["current_period_start"]
            )
        if "current_period_end" in kwargs:
            update_data["current_period_end"] = self._convert_datetime_to_isoformat(
                kwargs["current_period_end"]
            )
        if "cancel_at_period_end" in kwargs:
            update_data["cancel_at_period_end"] = (
                1 if kwargs["cancel_at_period_end"] else 0
            )

        for key, value in kwargs.items():
            if key not in [
                "current_period_start",
                "current_period_end",
                "cancel_at_period_end",
            ]:
                update_data[key] = value

        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.datastore.update("subscriptions", subscription_id, update_data)
        return self.get_subscription_by_id(subscription_id)

    def handle_stripe_webhook(self, event_payload: dict) -> dict | None:
        event_type = event_payload.get("type")

        if event_type == "checkout.session.completed":
            session = event_payload["data"]["object"]
            customer_id = session["customer"]
            subscription_id = session["subscription"]
            # Assuming you store tier_id in metadata or can derive it
            # For now, let's assume tier_id is passed in client_reference_id or similar
            # Or, we fetch the subscription from Stripe to get the price/product ID

            # Fetch subscription from Stripe to get details
            stripe_subscription = self.payment_gateway.stripe.get_subscription(
                subscription_id
            )  # Assuming this method exists
            if not stripe_subscription:
                self.logger.error(
                    f"Error: Stripe subscription {subscription_id} not found."
                )
                raise ValueError(
                    f"Error: Stripe subscription {subscription_id} not found."
                )

            # Get tier based on Stripe product ID
            stripe_product_id = stripe_subscription["items"]["data"][0]["price"][
                "product"
            ]
            tier = None
            all_tiers = self.datastore.get_all("tiers")
            for t_data in all_tiers:
                if t_data["stripe_product_id"] == stripe_product_id:
                    tier = self.get_tier_by_id(t_data["id"])
                    break

            if not tier:
                all_tiers_debug = self.datastore.get_all("tiers")
                self.logger.error(
                    f"Error: Tier not found for Stripe product ID {stripe_product_id}. All tiers: {all_tiers_debug}"
                )
                raise ValueError(
                    f"Error: Tier not found for Stripe product ID {stripe_product_id}."
                )

            # Create account and user if they don't exist
            # For simplicity, let's assume customer_id is linked to an account in our system
            # Or, create a new account and user for this subscription
            # For now, let's create a new account and user
            account_name = f"Stripe Customer {customer_id}"
            account = self.multi_tenant_manager.create_account(
                account_name
            )  # Assuming multi_tenant_manager is available
            

            # Create subscription record
            subscription = self.create_subscription(
                account.id,
                tier.id,
                stripe_subscription["id"],
                stripe_subscription["status"],
                datetime.fromtimestamp(
                    stripe_subscription["current_period_start"], tz=timezone.utc
                ),
                datetime.fromtimestamp(
                    stripe_subscription["current_period_end"], tz=timezone.utc
                ),
                stripe_subscription["cancel_at_period_end"],
            )

            return subscription  # Return the Subscription object

        # Add other webhook event types here (e.g., invoice.payment_succeeded, customer.subscription.updated)
        return None

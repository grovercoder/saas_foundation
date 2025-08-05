import pytest
import os
import sqlite3
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone

from src.datastore.manager import DatastoreManager
from src.datastore.database import get_db_connection, execute_query
from src.authorization.manager import AuthorizationManager
from src.payment_gateway.manager import PaymentGatewayManager
from src.subscription.manager import SubscriptionManager, MODULE_PERMISSIONS
from src.subscription.models import Limit, Feature, Tier, Subscription

# Use an in-memory database for testing
@pytest.fixture(scope="function")
def db_connection():
    original_db_url = os.getenv("DATABASE_URL")

    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    conn = get_db_connection()
    yield conn
    conn.close()

    if original_db_url is not None:
        os.environ["DATABASE_URL"] = original_db_url
    else:
        del os.environ["DATABASE_URL"]

    

@pytest.fixture(scope="function")
def setup_subscription_db(db_connection):
    # Ensure tables are clean before each test
    execute_query("DROP TABLE IF EXISTS subscriptions")
    execute_query("DROP TABLE IF EXISTS tiers")
    execute_query("DROP TABLE IF EXISTS features")
    execute_query("DROP TABLE IF EXISTS limits")

    datastore_manager = DatastoreManager([Limit, Feature, Tier, Subscription])
    yield datastore_manager

@pytest.fixture(scope="function")
def auth_manager():
    return AuthorizationManager()

@pytest.fixture(scope="function")
def mock_stripe_adapter():
    with patch('stripe.Product.create') as mock_product_create:
        with patch('stripe.Product.delete') as mock_product_delete:
            with patch('stripe.Subscription.retrieve') as mock_subscription_retrieve:
                adapter = MagicMock()
                mock_product_create.return_value = {'id': 'prod_test_123'}
                adapter.create_product = mock_product_create
                adapter.delete_product = mock_product_delete
                adapter.get_subscription = mock_subscription_retrieve # Add mock for get_subscription
                yield adapter

@pytest.fixture(scope="function")
def payment_gateway_manager(mock_stripe_adapter):
    return PaymentGatewayManager(adapters={"stripe": mock_stripe_adapter})

@pytest.fixture(scope="function")
def multi_tenant_manager(setup_subscription_db, auth_manager):
    # We need a real MultiTenantManager for subscription tests
    from src.multi_tenant.manager import MultiTenantManager as RealMultiTenantManager
    return RealMultiTenantManager(setup_subscription_db, auth_manager)

@pytest.fixture(scope="function")
def subscription_manager(setup_subscription_db, payment_gateway_manager, 
auth_manager, multi_tenant_manager):
    import importlib
    import src.subscription.manager
    importlib.reload(src.subscription.manager) # Force reload
    from src.subscription.manager import SubscriptionManager as RealSubscriptionManager # Explicit import
    return RealSubscriptionManager(
        datastore_manager=setup_subscription_db,
        payment_gateway_manager=payment_gateway_manager,
        authorization_manager=auth_manager,
        multi_tenant_manager=multi_tenant_manager
    )


def test_subscription_manager_registers_permissions(auth_manager, setup_subscription_db, payment_gateway_manager, multi_tenant_manager):
    # Instantiate SubscriptionManager to trigger permission registration
    SubscriptionManager(
        datastore_manager=setup_subscription_db,
        payment_gateway_manager=payment_gateway_manager,
        authorization_manager=auth_manager,
        multi_tenant_manager=multi_tenant_manager
    )
    registered_permissions = auth_manager.get_registered_permissions()
    assert len(registered_permissions) >= len(MODULE_PERMISSIONS) # May have other modules registered
    for perm in MODULE_PERMISSIONS:
        assert perm in registered_permissions


def test_create_limit(subscription_manager):
    limit = subscription_manager.create_limit("max_users", "Maximum Users", "Max number of users per account", 10)
    assert isinstance(limit, Limit)
    assert limit.key == "max_users"
    assert limit.default_value == 10

    retrieved_limit = subscription_manager.get_limit_by_key("max_users")
    assert retrieved_limit == limit


def test_create_feature(subscription_manager):
    feature = subscription_manager.create_feature("api_access", "API Access", "Allows API access", ["api:read", "api:write"])
    assert isinstance(feature, Feature)
    assert feature.key == "api_access"
    assert "api:read" in feature.permissions

    retrieved_feature = subscription_manager.get_feature_by_key("api_access")
    assert retrieved_feature == feature


def test_create_tier(subscription_manager, mock_stripe_adapter):
    # Create a limit and feature first
    limit = subscription_manager.create_limit("storage_gb", "Storage (GB)", "Max storage in GB", 50)
    feature = subscription_manager.create_feature("reporting", "Reporting", "Advanced reporting features", ["report:view"])

    tier = subscription_manager.create_tier(
        "basic", "Basic Plan", "Entry level plan", 10.00, 100.00,
        features=["reporting"], limits={"storage_gb": 100}
    )

    assert isinstance(tier, Tier)
    assert tier.key == "basic"
    assert tier.status == "draft"
    assert tier.monthly_cost == 10.00
    assert tier.yearly_cost == 100.00
    assert "reporting" in tier.features
    assert tier.limits["storage_gb"] == 100
    # mock_stripe_adapter.create_product.assert_called_once() # Uncomment when Stripe product creation is active

    retrieved_tier = subscription_manager.get_tier_by_key("basic")
    assert retrieved_tier == tier


def test_update_tier(subscription_manager):
    tier = subscription_manager.create_tier(
        "update_test", "Update Test Plan", "", 5.00, 50.00
    )
    updated_tier = subscription_manager.update_tier(
        tier.id, name="Updated Name", monthly_cost=15.00
    )
    assert updated_tier.name == "Updated Name"
    assert updated_tier.monthly_cost == 15.00
    assert updated_tier.updated_at >= tier.created_at


def test_deactivate_and_activate_tier(subscription_manager):
    tier = subscription_manager.create_tier(
        "status_test", "Status Test Plan", "", 20.00, 200.00
    )
    deactivated_tier = subscription_manager.deactivate_tier(tier.id)
    assert deactivated_tier.status == "deactivated"

    activated_tier = subscription_manager.activate_tier(tier.id, status="active:private")
    assert activated_tier.status == "active:private"


def test_delete_tier(subscription_manager):
    tier = subscription_manager.create_tier(
        "delete_test", "Delete Test Plan", "", 1.00, 10.00
    )
    # Must be deactivated first
    subscription_manager.deactivate_tier(tier.id)
    subscription_manager.delete_tier(tier.id)

    retrieved_tier = subscription_manager.get_tier_by_key("delete_test")
    assert retrieved_tier is None

    with pytest.raises(ValueError, match="Tier with ID .* must be deactivated before deletion."):
        tier_active = subscription_manager.create_tier("delete_fail", "Delete Fail", "", 1.00, 10.00)
        subscription_manager.delete_tier(tier_active.id)


def test_create_subscription_and_webhook_handling(subscription_manager, multi_tenant_manager, mock_stripe_adapter):
    # Setup: Create a tier that the subscription will be for
    tier = subscription_manager.create_tier(
        "premium", "Premium Plan", "Full access", 50.00, 500.00,
        stripe_product_id="prod_test_123"
    )

    # Mock Stripe subscription retrieve
    mock_stripe_adapter.get_subscription.return_value = {
        'id': 'sub_test_123',
        'status': 'active',
        'current_period_start': int(datetime.now(timezone.utc).timestamp()),
        'current_period_end': int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp()),
        'cancel_at_period_end': False,
        'items': {
            'data': [{'price': {'product': "prod_test_123"}}]
        }
    }

    # Simulate a Stripe checkout.session.completed webhook event
    event_payload = {
        'type': 'checkout.session.completed',
        'data': {
            'object': {
                'customer': 'cus_test_123',
                'subscription': 'sub_test_123',
                'client_reference_id': 'some_ref_id' # Could contain tier_id or account_id
            }
        }
    }

    # Handle the webhook
    subscription = subscription_manager.handle_stripe_webhook(event_payload)

    assert subscription is not None
    assert subscription.stripe_subscription_id == 'sub_test_123'
    assert subscription.status == 'active'
    assert int(subscription.tier_id) == tier.id
    assert subscription.account_id is not None

    # Verify that an account and user were created
    account = multi_tenant_manager.get_account_by_id(subscription.account_id)
    assert account is not None
    assert account.name == f"Stripe Customer cus_test_123"

    # Verify that the subscription can be retrieved by its ID and Stripe ID
    retrieved_sub_by_id = subscription_manager.get_subscription_by_id(subscription.id)
    assert retrieved_sub_by_id == subscription

    retrieved_sub_by_stripe_id = subscription_manager.get_subscription_by_stripe_id('sub_test_123')
    assert retrieved_sub_by_stripe_id == subscription

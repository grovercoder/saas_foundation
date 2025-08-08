import pytest
import os
from unittest.mock import MagicMock, patch

# Mock environment variables for DatastoreManager
@pytest.fixture(autouse=True)
def mock_env_vars():
    with patch.dict(os.environ, {'DB_PATH': '/tmp/test_db', 'DB_NAME': 'test_db'}):
        yield

# Mock the actual manager classes to prevent real initialization side effects
class MockLogManager(MagicMock):
    pass

class MockDataStoreManager(MagicMock):
    pass

class MockPaymentGatewayManager(MagicMock):
    pass

class MockMultiTenantManager(MagicMock):
    pass

class MockAuthorizationManager(MagicMock):
    pass

class MockSubscriptionManager(MagicMock):
    pass

# Patch the imports within saas_foundation.manager
@pytest.fixture(autouse=True)
def patch_managers():
    with (
        patch('saas_foundation.manager.LogManager', MockLogManager),
        patch('saas_foundation.manager.DatastoreManager', MockDataStoreManager),
        patch('saas_foundation.manager.PaymentGatewayManager', MockPaymentGatewayManager),
        patch('saas_foundation.manager.MultiTenantManager', MockMultiTenantManager),
        patch('saas_foundation.manager.AuthorizationManager', MockAuthorizationManager),
        patch('saas_foundation.manager.SubscriptionManager', MockSubscriptionManager)
    ):
        yield


from saas_foundation.manager import SaasManager

def test_saas_manager_initialization():
    saas_manager = SaasManager()
    assert isinstance(saas_manager, SaasManager)

def test_get_log_manager():
    saas_manager = SaasManager()
    log_manager = saas_manager.get_log_manager()
    assert isinstance(log_manager, MockLogManager)
    assert saas_manager.log_manager is log_manager

def test_get_datastore_manager():
    saas_manager = SaasManager()
    datastore_manager = saas_manager.get_datastore_manager()
    assert isinstance(datastore_manager, MockDataStoreManager)
    assert saas_manager.datastore_manager is datastore_manager

def test_get_payment_gateway_manager():
    saas_manager = SaasManager()
    payment_gateway_manager = saas_manager.get_payment_gateway_manager()
    assert isinstance(payment_gateway_manager, MockPaymentGatewayManager)
    assert saas_manager.payment_gateway_manager is payment_gateway_manager

def test_get_multi_tenant_manager():
    saas_manager = SaasManager()
    multi_tenant_manager = saas_manager.get_multi_tenant_manager()
    assert isinstance(multi_tenant_manager, MockMultiTenantManager)
    assert saas_manager.multi_tenant_manager is multi_tenant_manager

def test_get_authorization_manager():
    saas_manager = SaasManager()
    authorization_manager = saas_manager.get_authorization_manager()
    assert isinstance(authorization_manager, MockAuthorizationManager)
    assert saas_manager.authorization_manager is authorization_manager

def test_get_subscription_manager():
    saas_manager = SaasManager()
    subscription_manager = saas_manager.get_subscription_manager()
    assert isinstance(subscription_manager, MockSubscriptionManager)
    assert saas_manager.subscription_manager is subscription_manager

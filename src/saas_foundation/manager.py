
import os

from saas_foundation.logging_system.manager import LogManager
from saas_foundation.datastore.manager import DatastoreManager
from saas_foundation.payment_gateway.manager import PaymentGatewayManager
from saas_foundation.multi_tenant.manager import MultiTenantManager
from saas_foundation.authorization.manager import AuthorizationManager
from saas_foundation.subscription.manager import SubscriptionManager


class SaasManager:
    def __init__(self, db_path: str = None, db_name: str = None):
        # Initialize LogManager first as other managers might use it
        self.log_manager = LogManager()

        # Initialize DatastoreManager
        # If db_path or db_name are not provided, DataStoreManager will attempt to get them from environment variables
        self.datastore_manager = DatastoreManager(self.log_manager.get_logger())

        # Initialize other managers that do not have complex dependencies yet
        self.payment_gateway_manager = PaymentGatewayManager()

        # Initialize MultiTenantManager, which depends on DatastoreManager
        self.multi_tenant_manager = MultiTenantManager(datastore_manager=self.datastore_manager)

        # Initialize AuthorizationManager, which depends on DatastoreManager
        self.authorization_manager = AuthorizationManager(datastore_manager=self.datastore_manager)

        # Initialize SubscriptionManager, which depends on several other managers
        self.subscription_manager = SubscriptionManager(
            log_manager=self.log_manager,
            datastore_manager=self.datastore_manager,
            payment_gateway_manager=self.payment_gateway_manager,
            multi_tenant_manager=self.multi_tenant_manager,
            authorization_manager=self.authorization_manager
        )

    def get_log_manager(self) -> LogManager:
        return self.log_manager

    def get_datastore_manager(self) -> DatastoreManager:
        return self.datastore_manager

    def get_payment_gateway_manager(self) -> PaymentGatewayManager:
        return self.payment_gateway_manager

    def get_multi_tenant_manager(self) -> MultiTenantManager:
        return self.multi_tenant_manager

    def get_authorization_manager(self) -> AuthorizationManager:
        return self.authorization_manager

    def get_subscription_manager(self) -> SubscriptionManager:
        return self.subscription_manager

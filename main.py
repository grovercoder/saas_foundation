from dotenv import load_dotenv
import argparse
from src.datastore.manager import DatastoreManager
from src.multi_tenant.manager import MultiTenantManager
from src.payment_gateway.manager import PaymentGatewayManager
from src.authorization.manager import AuthorizationManager
from src.subscription.manager import SubscriptionManager
from src.logging_system.manager import LogManager
from src.email_services.manager import EmailManager
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class User:
    id: int
    name: str
    email: str

@dataclass
class Product:
    id: int
    product_name: str
    price: float

def main():
    load_dotenv() # Load environment variables from .env file

    parser = argparse.ArgumentParser(description="Library Orchestration Application")
    parser.add_argument("--mode", type=str, default="dev",
                        help="Application mode (e.g., 'dev', 'run_workflow')")
    parser.add_argument("--workflow_id", type=str,
                        help="ID of the workflow to execute (if mode is 'run_workflow')")

    args = parser.parse_args()

    log_manager = LogManager()
    logger = log_manager.get_logger()
    logger.info("Application started.")

    email_manager = EmailManager(logger)

    print("Running in development mode.")
    # Initialize DatastoreManager with models
    datastore_manager = DatastoreManager(logger, [User, Product])

    # Ensure tables are clean before each run in dev mode
    datastore_manager.execute_query("DROP TABLE IF EXISTS users")
    datastore_manager.execute_query("DROP TABLE IF EXISTS accounts")
    datastore_manager.execute_query("DROP TABLE IF EXISTS limits")
    datastore_manager.execute_query("DROP TABLE IF EXISTS features")
    datastore_manager.execute_query("DROP TABLE IF EXISTS tiers")
    datastore_manager.execute_query("DROP TABLE IF EXISTS subscriptions")

    authorization_manager = AuthorizationManager(logger)
    payment_gateway_manager = PaymentGatewayManager(logger)
    multi_tenant_manager = MultiTenantManager(logger, datastore_manager, authorization_manager)
    subscription_manager = SubscriptionManager(logger, datastore_manager, payment_gateway_manager, authorization_manager)

    # Placeholder for future workflow execution or other service-level operations
    logger.info(f"Application running in {args.mode} mode.")

if __name__ == "__main__":
    main()
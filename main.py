from dotenv import load_dotenv
import argparse
from src.datastore.manager import DatastoreManager
from src.multi_tenant.manager import MultiTenantManager
from src.payment_gateway.manager import PaymentGatewayManager
from src.authorization.manager import AuthorizationManager
from src.subscription.manager import SubscriptionManager
from src.logging_system.manager import LogManager
from src.templating.manager import TemplatingManager
from src.email_services.manager import EmailManager
from src.web_service.app import initialize_web_service
from src.web_service.routes import public as public_routes
import uvicorn
import asyncio
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

    templating_manager = TemplatingManager(logger)
    email_manager = EmailManager(logger, templating_manager)

    # REMOVING THIS CODE temporarily for development purposes
    # if args.mode == "dev":
    #     print("Running in development mode.")
    #     # Initialize DatastoreManager with models
    #     datastore_manager = DatastoreManager([User, Product])

    #     # Ensure tables are clean before each run in dev mode
    #     datastore_manager.execute_query("DROP TABLE IF EXISTS users")
    #     datastore_manager.execute_query("DROP TABLE IF EXISTS accounts")
    #     datastore_manager.execute_query("DROP TABLE IF EXISTS limits")
    #     datastore_manager.execute_query("DROP TABLE IF EXISTS features")
    #     datastore_manager.execute_query("DROP TABLE IF EXISTS tiers")
    #     datastore_manager.execute_query("DROP TABLE IF EXISTS subscriptions")

    #     authorization_manager = AuthorizationManager()
    #     payment_gateway_manager = PaymentGatewayManager()
    #     multi_tenant_manager = MultiTenantManager(datastore_manager, authorization_manager)
    #     subscription_manager = SubscriptionManager(datastore_manager, payment_gateway_manager, authorization_manager)

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

    web_service = initialize_web_service(logger, templating_manager, None, args.mode) # Pass None for server initially, and the mode
    web_service.get_app().include_router(public_routes.router)

    config = uvicorn.Config(web_service.get_app(), host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)

    # Now set the server instance on the web_service after it's created
    web_service.set_server(server)

    if args.mode == "dev":
        async def run_server():
            await server.serve()

        asyncio.run(run_server())

if __name__ == "__main__":
    main()
    
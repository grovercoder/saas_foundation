from dotenv import load_dotenv
import argparse
from src.datastore.schema import create_tables_from_entity_definitions
from src.datastore.manager import DatastoreManager
from src.multi_tenant.manager import MultiTenantManager
from src.payment_gateway.manager import PaymentGatewayManager
from src.authorization.manager import AuthorizationManager

def main():
    load_dotenv() # Load environment variables from .env file

    parser = argparse.ArgumentParser(description="Library Orchestration Application")
    parser.add_argument("--mode", type=str, default="dev",
                        help="Application mode (e.g., 'dev', 'run_workflow')")
    parser.add_argument("--workflow_id", type=str,
                        help="ID of the workflow to execute (if mode is 'run_workflow')")

    args = parser.parse_args()

    print(f"Application started in {args.mode} mode.")

    if args.mode == "dev":
        print("Running in development mode.")
        # Placeholder for entity definitions from external library discovery
        example_entity_definitions = {
            "users": {
                "name": "TEXT NOT NULL",
                "email": "TEXT UNIQUE NOT NULL"
            },
            "products": {
                "product_name": "TEXT NOT NULL",
                "price": "REAL"
            }
        }
        datastore_manager = DatastoreManager(example_entity_definitions)
        multi_tenant_manager = MultiTenantManager(datastore_manager, authorization_manager)
        payment_gateway_manager = PaymentGatewayManager()
        authorization_manager = AuthorizationManager()

        # Example: Registering permissions
        example_permissions = [
            {"key": "user:create", "name": "Users Create", "description": "Can create new user accounts."},
            {"key": "user:read", "name": "Users Read", "description": "Can view user account details."},
            {"key": "account:manage", "name": "Account Management", "description": "Can manage account settings."}
        ]
        try:
            authorization_manager.register_permissions(example_permissions)
            print("Permissions registered successfully.")
            print("Registered permissions:", authorization_manager.get_registered_permissions())
        except ValueError as e:
            print(f"Error registering permissions: {e}")

        # Example usage of multi_tenant_manager
        try:
            account = multi_tenant_manager.create_account("Test Account")
            print(f"Created account: {account.name} with ID: {account.id}")

            user = multi_tenant_manager.create_user(account.id, "testuser", "password123")
            print(f"Created user: {user.username} with ID: {user.id} in account: {user.account_id}")

            authenticated_user = multi_tenant_manager.authenticate_user("testuser", "password123")
            if authenticated_user:
                print(f"User {authenticated_user.username} authenticated successfully.")
            else:
                print("Authentication failed.")

            reset_token = multi_tenant_manager.set_reset_token(user.id)
            print(f"Set reset token for user {user.username}: {reset_token}")

            if multi_tenant_manager.verify_reset_token(user.id, reset_token):
                print("Reset token verified.")
                multi_tenant_manager.reset_password(user.id, "newpassword", reset_token)
                print("Password reset successfully.")
            else:
                print("Reset token verification failed.")

            if multi_tenant_manager.authenticate_user("testuser", "newpassword"):
                print(f"User {user.username} authenticated with new password.")

            # Example usage of payment_gateway_manager (Stripe)
            # Note: This will require valid Stripe API keys and potentially a running Stripe webhook endpoint
            # try:
            #     customer = payment_gateway_manager.stripe.create_customer("customer@example.com", "Test Customer")
            #     print(f"Created Stripe customer: {customer['id']}")
            # except ValueError as e:
            #     print(f"Error creating Stripe customer: {e}")

        except Exception as e:
            print(f"Error during multi-tenant setup: {e}")

        # Add development-specific logic here
    elif args.mode == "run_workflow":
        if args.workflow_id:
            print(f"Executing workflow with ID: {args.workflow_id}")
            # Add workflow execution logic here
        else:
            print("Error: --workflow_id is required for 'run_workflow' mode.")
    else:
        print(f"Unknown mode: {args.mode}")

if __name__ == "__main__":
    main()
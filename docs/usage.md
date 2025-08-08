# Usage Guide

This guide provides detailed instructions on how to use the "Foundation" library, covering setup, core module interactions, and common workflows.

## 1. Setup

For initial project setup and dependency installation, please refer to the [README.md](../README.md) file.

Ensure your environment variables are correctly configured as described in the README, especially for database, Stripe, and email services.

## 2. Using the Datastore

The Datastore Module provides direct database interaction using SQLite3, without an ORM. It supports dynamic entity definition registration and automatic DAO generation.

### Initialization

To use the datastore, you typically initialize the `DatastoreManager`:

```python
import os
from saas_foundation.datastore.manager import DatastoreManager

# Ensure environment variables are set (e.g., from a .env file)
os.environ['DB_PATH'] = os.getenv('DB_PATH', './data')
os.environ['DB_NAME'] = os.getenv('DB_NAME', 'my_application.db')

# Initialize the DatastoreManager
datastore_manager = DatastoreManager()

# Get a database connection
db_connection = datastore_manager.get_db_connection()
print(f"Connected to database: {db_connection}")

# Remember to close the connection when done
db_connection.close()
```

### Entity Definition Registration

External libraries or other modules can register their data models (entities) with the Datastore Module. These models are typically `dataclass` objects. The Datastore Module uses these definitions to create database tables and generate Data Access Objects (DAOs).

```python
from dataclasses import dataclass
from saas_foundation.datastore.manager import DatastoreManager

@dataclass
class MyEntity:
    id: int = None
    name: str = None
    value: str = None

# Assuming datastore_manager is already initialized
datastore_manager.register_entity_definition(MyEntity)

# This will create the 'my_entity' table if it doesn't exist
# and make DAOs available for MyEntity.
```

### Performing Database Operations (via DAOs)

After registering an entity, you can obtain a DAO for it and perform CRUD operations.

```python
# Assuming MyEntity has been registered
my_entity_dao = datastore_manager.get_dao(MyEntity)

# Create a new entity
new_entity = MyEntity(name="Test Item", value="Some Data")
created_entity = my_entity_dao.create(new_entity)
print(f"Created entity: {created_entity}")

# Read entities
all_entities = my_entity_dao.read_all()
print(f"All entities: {all_entities}")

# Read by ID
retrieved_entity = my_entity_dao.read_by_id(created_entity.id)
print(f"Retrieved entity by ID: {retrieved_entity}")

# Update an entity
retrieved_entity.value = "Updated Data"
updated_entity = my_entity_dao.update(retrieved_entity)
print(f"Updated entity: {updated_entity}")

# Delete an entity
my_entity_dao.delete(updated_entity.id)
print(f"Deleted entity with ID: {updated_entity.id}")
```

## 3. Using the Authorization System

The Authorization System provides a hybrid RBAC (Role-Based Access Control) mechanism for managing user permissions and access control. Other modules can register their exposed permissions with this system.

### Initialization

```python
from saas_foundation.authorization.manager import AuthorizationManager

auth_manager = AuthorizationManager()
```

### Registering Permissions

Modules can register their specific permissions:

```python
# Example: A hypothetical 'document_management' module registering permissions
auth_manager.register_permissions(
    "document_management",
    ["document:create", "document:read", "document:update", "document:delete"]
)

# Example: Multi-tenant module registering its permissions (as defined in its manager)
from saas_foundation.multi_tenant.manager import MultiTenantManager

multi_tenant_manager = MultiTenantManager(datastore_manager=datastore_manager, auth_manager=auth_manager)
multi_tenant_manager.register_permissions()
```

### Checking Permissions

To check if a user (or a role associated with a user) has a specific permission:

```python
# Assuming you have a user object or user ID
user_id = 123
permission_key = "document:read"

if auth_manager.has_permission(user_id, permission_key):
    print(f"User {user_id} has permission: {permission_key}")
else:
    print(f"User {user_id} does NOT have permission: {permission_key}")
```

## 4. Defining Limits, Features, and Tiers (Subscription Management)

The Subscription Management module allows you to define subscription tiers, features, and limits, which are crucial for multi-tenant SaaS applications.

### Initialization

```python
from saas_foundation.subscription.manager import SubscriptionManager
from saas_foundation.payment_gateway.manager import PaymentGatewayManager

# Assuming datastore_manager and auth_manager are initialized
payment_gateway_manager = PaymentGatewayManager()
subscription_manager = SubscriptionManager(
    datastore_manager=datastore_manager,
    payment_gateway_manager=payment_gateway_manager
)
```

### Defining Limits

Limits define quantifiable restrictions that can be applied to a tier (e.g., maximum users, storage space).

```python
# Define a limit
max_users_limit = subscription_manager.define_limit(
    key="max_users",
    name="Maximum Users",
    description="The maximum number of users allowed per account.",
    default_value=5
)
print(f"Defined Limit: {max_users_limit}")
```

### Defining Features

Features define capabilities provided by a tier and are associated with specific permissions.

```python
# Define a feature
premium_support_feature = subscription_manager.define_feature(
    key="premium_support",
    name="Premium Support",
    description="Access to 24/7 premium customer support.",
    permissions=["support:premium_access", "support:priority_queue"]
)
print(f"Defined Feature: {premium_support_feature}")
```

### Defining Tiers

Tiers combine features and limits to create different subscription plans. When a tier is created, a corresponding Stripe product is also created.

```python
from saas_foundation.subscription.models import TierStatus

# Define a tier
basic_tier = subscription_manager.define_tier(
    key="basic",
    status=TierStatus.ACTIVE_PUBLIC,
    name="Basic Plan",
    description="Our entry-level plan.",
    monthly_cost=10.00,
    yearly_cost=100.00,
    feature_keys=["premium_support"], # Use the key of the feature defined above
    limits={
        "max_users": 10 # Apply a specific value for the 'max_users' limit
    }
)
print(f"Defined Tier: {basic_tier}")
```

## 5. Signing Up a New Account

The Multi-tenant Management module handles account and user creation. When a user subscribes via Stripe, an account and a default user are created if they don't already exist.

### Handling Stripe Webhooks (`checkout.session.completed`)

When a `checkout.session.completed` webhook is received from Stripe, the `SubscriptionManager` processes it to create the subscription record, account, and default user.

```python
# This is typically handled by your webhook endpoint. 
# The payload would come from Stripe.
stripe_webhook_payload = {
    # ... actual Stripe checkout.session.completed event payload ...
    "id": "evt_123",
    "type": "checkout.session.completed",
    "data": {
        "object": {
            "id": "cs_test_123",
            "customer": "cus_abc",
            "subscription": "sub_xyz",
            "metadata": {
                "tier_key": "basic", # The key of the tier the user subscribed to
                "user_email": "user@example.com",
                "user_password": "securepassword" # In a real app, this would be hashed or handled differently
            }
        }
    }
}

# Assuming subscription_manager is initialized
# The process_stripe_webhook method would parse the event and create records
# Note: In a real application, you would verify the webhook signature.
# This example simplifies the process for demonstration.

# subscription_manager.process_stripe_webhook(stripe_webhook_payload)
# This method would internally call multi_tenant_manager to create account/user
```

### Manual Account and User Creation (for testing or specific flows)

While Stripe webhooks handle the primary signup flow, you can also manually create accounts and users using the `MultiTenantManager`.

```python
from saas_foundation.multi_tenant.manager import MultiTenantManager

# Assuming datastore_manager and auth_manager are initialized
multi_tenant_manager = MultiTenantManager(
    datastore_manager=datastore_manager,
    auth_manager=auth_manager
)

# Create an account
new_account = multi_tenant_manager.create_account("My New Company")
print(f"Created Account: {new_account}")

# Create a user for the account
new_user = multi_tenant_manager.create_user(
    account_id=new_account.id,
    username="newuser@example.com",
    password="verysecurepassword123"
)
print(f"Created User: {new_user}")
```

## 6. Authenticating Users

User authentication is handled by the Multi-tenant Management module, which includes password hashing and verification.

```python
# Assuming multi_tenant_manager is initialized

username = "newuser@example.com"
password = "verysecurepassword123"

authenticated_user = multi_tenant_manager.authenticate_user(username, password)

if authenticated_user:
    print(f"User {authenticated_user.username} authenticated successfully.")
    # You can now use authenticated_user.id for authorization checks
else:
    print("Authentication failed.")
```

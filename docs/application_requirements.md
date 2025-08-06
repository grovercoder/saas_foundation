# **Initial Requirements for a Library Orchestration Application**

### **Vision**

This project, "Foundation," is a pure service-level library designed to provide core multi-tenant SaaS services and a robust datastorage solution. Its primary purpose is to offer foundational backend capabilities, ensuring a clear separation of concerns from any presentation-layer elements.

### **Core Purpose**

The "Foundation" project focuses exclusively on backend service logic. Any functionality related to "how something looks" (e.g., web interfaces, UI components, direct templating for presentation) is considered a presentation-level concern and does not belong within this project. These presentation aspects will be handled by a separate integration project, which will serve as the ultimate "application" built upon this foundational service layer.

### **Core Concepts**

* **Orchestration Layer:** This is the application itself. It provides the central logic for managing workflows, communicating with external libraries, and handling system-level concerns like security and error handling.  
* **External Libraries:** These are the custom solutions that provide the actual business logic and core functionality. They are built and maintained outside of this application.  
* **Internal Systems:** These are core libraries that, while part of the application, are developed as separate packages to provide foundational services like data persistence and user management.  
* **Connectors/Adapters:** These are the interfaces that allow the orchestration layer to communicate with the specific APIs of each external library. A well-designed connector will translate the orchestration layer's requests into a format that the external library can understand and vice-versa.  
* **Dependency Injection:** The application will be designed to create and manage objects from these internal and external systems, injecting them into other components as dependencies. For example, a MultiTenants object would be created and injected with a Datastore object.

### **Functional Requirements**

* **Library Management:** The system must provide a way to **add, remove, and update** external libraries dynamically without requiring a full application redeploy.  
* **Capability Registration:** Instead of dynamic discovery, external libraries will explicitly **register** their specific functions, permissions, and capabilities with the appropriate manager objects during their initialization. This ensures a clear and controlled integration process.
  * **Entity Definition Registration:** External libraries must register their entity definitions (e.g., required database tables and fields) with the **Datastore Module** during initialization. The Datastore Module will use these dataclass models to automatically create the necessary database tables and generate corresponding Data Access Objects (DAOs) for use by the orchestrator.  
* **Workflow Definition:** Users must be able to define and configure **multi-step workflows** that chain together capabilities from different external libraries.  
* **Execution Engine:** The application must have a robust engine for executing these workflows, handling the sequence of calls to external libraries and managing the flow of data between them.  
* **Configuration:** The system should allow for easy configuration of each external library, such as API keys, endpoints, and specific parameters required for its operation.  
* **Error Handling:** It needs to implement a comprehensive strategy for handling errors originating from external libraries, including **retries, fallbacks, and notifications**.

### **Internal Systems & Module Requirements**

The application will include the following internal modules to provide core functionality:

*   **Datastore Module:**
    *   The module will be a separate package within the application.
    *   It must use **SQLite3** for all database operations.
    *   It will **not** use an Object-Relational Mapper (ORM), relying on direct database queries.
    *   It will retrieve database connection details (DB_PATH, DB_NAME, DB_PORT, DB_USER, DB_PASS) from environment variables, which will be loaded from a .env file.
    *   The system will ensure the database directory (DB_PATH) exists, creating it if necessary.
    *   All exposed ID values from the datastore will be integer IDs.
*   **Logging System:**
    *   A dedicated module for centralized logging.
    *   It should provide a consistent interface for other modules to log messages.
    *   Support for different log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    *   Configurable output destinations (e.g., console, file).
*   **Multi-tenant Management:** This system will handle the management of accounts, account users, and their associated roles. Users must belong to an existing account. User records will include a username, a hashed password (never plain text), a reset token, and the timestamp the token was created. This module will also define and register its own specific permissions with the Authorization System.
*   **Payment Gateway Wrapper:** A module that provides a consistent interface for interacting with various payment gateways. It will include a **Stripe adapter** that utilizes the Stripe API and provides a method to handle webhook events.
*   **Subscription Management:** This system will handle the setup and management of user subscriptions. It consists of two main parts:
    *   **Tier/Feature/Limit Management:** Defines **subscription tiers**, associated **features**, and specific **limits** (such as maximum users or storage).
        *   **Limits:** Define things that might need to be limited in a tier. They have a "key", "name", "description", and "default_value". The specific value to apply to a limit is set when the limit is added to a tier. A tier may have zero or more limits.
        *   **Features:** Define capabilities provided by a tier. They have a "key", "name", "description", and a list of "permissions" (keys for relevant permissions a feature must have). These permissions become the default list to check for when verifying a user's authorization based on their account's tier.
        *   **Tiers:** Consist of "key", "status", "name", "description", "monthly_cost", "yearly_cost", "features" (list of feature keys), and "limits" (dictionary of limit_key: value).
        *   When a tier is created, a database record is created. A corresponding Stripe product is also created.
        *   A tier cannot be removed unless it is deactivated (status set to "deactivated"). It cannot be deactivated unless the tier has no active accounts associated with it.
        *   Tier status can be set to "active:public", "active:private", " "draft", or "deactivated".
    *   **Subscription Management:** Handles creating, updating, and managing individual subscriptions.
        *   When a user subscribes, the Stripe Webhook for `checkout.session.completed` is received.
        *   Upon receiving this webhook, a subscription record is created in the database.
        *   An account and a default user are created (if they don't already exist), and the account is linked to the subscription record, which also indicates the associated tier.
*   **Authorization System:** A system responsible for managing user permissions and access control to various parts of the application, utilizing a **hybrid role-based access control list (RBAC) system**. It provides a mechanism for other modules to register their exposed permissions.


*   **Email Services:**
    *   A custom library that provides SMTP services for sending and managing outgoing emails.
    *   It supports sending both HTML and plain text versions of email bodies as pre-rendered string content. Template rendering is handled externally by the calling application.


### **Presentation Layer**

Presentation-level concerns (e.g., web interfaces, UI components, direct templating for presentation) are explicitly excluded from this project. These aspects will be handled by a separate integration project, which will serve as the ultimate "application" built upon this foundational service layer. This separation ensures the "Foundation" project remains a pure service-level library, not bound to any specific web framework, templating solution, or frontend framework/look & feel.

### **Future Integration Projects**

A later project will be created to provide the web services, templating, and integrate application-specific service libraries (e.g., for dynamic forms and custom workflows). This approach ensures the "Foundation" project remains a pure service layer, decoupled from specific presentation or application-level concerns.

### **Development Environment & Standards**

* **Language:** Python  
* **Package Management:** The **uv** tool will be used for all package management.  
  * To initialize the project, run `uv init`.  
  * To add dependencies, use `uv add \<package\_name\>`.  
  * To run scripts or commands, use `uv run \<command\>`.  
  * To run tests use `uv run python -m pytest`
* **Code Standards:** The code must adhere to standards enforced by **black** for formatting and **pylint** for style and static analysis.  
* **Testing:** All unit and integration tests will be written using **pytest**. Tests should be run using the command uv run pytest.

### **Non-Functional Requirements**

* **Scalability:** The application's architecture must be designed to **scale horizontally**, allowing it to handle an increasing number of imported libraries and a high volume of simultaneous workflow executions.  
* **Reliability:** The system should be highly reliable and resilient. The failure of one external library should **not cause the entire orchestrator to fail**.  
* **Security:** It must include a robust security model for **authentication and authorization**, ensuring that only authorized users or systems can define and execute workflows.  
* **Performance:** The orchestration layer should add minimal latency to the overall workflow execution. Communication with external libraries should be **optimized for speed**.  
* **Maintainability:** The use of a modular design with clear separation of concerns (e.g., the orchestration engine and the connectors) will ensure the system is easy to maintain, debug, and upgrade.  
* **Observability:** The application must provide **logging and monitoring** capabilities to track workflow execution, success rates, and errors.

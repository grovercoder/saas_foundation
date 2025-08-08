# Foundation: Library Orchestration Application

## Project Vision

"Foundation" is a pure service-level library designed to provide core multi-tenant SaaS services and a robust datastorage solution. Its primary purpose is to offer foundational backend capabilities, ensuring a clear separation of concerns from any presentation-layer elements. This project focuses exclusively on backend service logic; presentation-layer concerns will be handled by separate integration projects.

## Core Concepts

*   **Orchestration Layer:** The application itself, managing workflows, communicating with external libraries, and handling system-level concerns (security, error handling).
*   **External Libraries:** Custom solutions providing business logic, maintained externally.
*   **Internal Systems:** Core libraries developed as separate packages within the application (e.g., data persistence, user management).
*   **Connectors/Adapters:** Interfaces for communication between the orchestration layer and external library APIs.
*   **Dependency Injection:** Design principle for managing and injecting objects from internal and external systems.

## Getting Started

### Installation

This project uses `uv` for package management.

1.  **Initialize the project:**
    ```bash
    uv init
    ```
2.  **Install dependencies:**
    ```bash
    uv pip install -r requirements.txt
    ```

### Running Tests

To run all unit and integration tests:

```bash
uv run python -m pytest
```

### Environment Variables

The following environment variables are used by the application. These should be loaded from a `.env` file in the project root.

#### Database Configuration

*   `DB_PATH`: (Optional) The directory where the SQLite database file will be stored. Defaults to `./data`.
*   `DB_NAME`: (Optional) The name of the SQLite database file. Defaults to `application.db`.

#### Stripe Integration

*   `STRIPE_SECRET_KEY`: Your Stripe secret API key.
*   `STRIPE_WEBHOOK_SECRET`: Your Stripe webhook secret for verifying webhook events.

#### Email Services

*   `SMTP_SERVER`: The SMTP server address.
*   `SMTP_PORT`: The SMTP server port (e.g., `587` for TLS).
*   `SMTP_USERNAME`: The username for SMTP authentication.
*   `SMTP_PASSWORD`: The password for SMTP authentication.
*   `SMTP_USE_TLS`: Set to `True` to enable TLS encryption for SMTP (e.g., `True` or `False`).
*   `SMTP_SENDER_EMAIL`: The email address to be used as the sender.

## Code Standards

*   **Formatting:** `black`
*   **Style & Static Analysis:** `pylint`

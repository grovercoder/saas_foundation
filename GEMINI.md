# Gemini Development Guidelines for Library Orchestration Application

This document outlines the core principles, technologies, and architectural patterns for developing the Library Orchestration Application. It is intended to guide the Gemini AI assistant in making informed decisions during development.

## 1. Project Vision & Core Purpose

The application serves as a central orchestration layer to manage and execute capabilities from external, custom-built libraries. Its primary purpose is to integrate and combine these external services into complex workflows, focusing on discovery, management, and reliable execution of imported capabilities.

## 2. Core Concepts & Architecture

*   **Orchestration Layer:** The application itself, managing workflows, communicating with external libraries, and handling system-level concerns (security, error handling).
*   **External Libraries:** Custom solutions providing business logic, maintained externally.
*   **Internal Systems:** Core libraries developed as separate packages within the application (e.g., data persistence, user management).
*   **Connectors/Adapters:** Interfaces for communication between the orchestration layer and external library APIs.
*   **Dependency Injection:** Design principle for managing and injecting objects from internal and external systems.

## 3. Key Technologies & Development Standards

Always review @docs/application_requirements.md to understand the intent of the application.

*   **Language:** Python
*   **Package Management:** `uv` tool.
    *   Initialize: `uv init`
    *   Add dependencies: `uv add <package_name>`
    *   Run commands: `uv run <command>`
*   **Code Standards:**
    *   Formatting: `black`
    *   Style & Static Analysis: `pylint`
*   **Testing:** `pytest` for all unit and integration tests.
    *   Run tests: `uv run python -m pytest`

*   **Revision Control**
    *   Use `git`
    *   Use the "summary / body" structure for commit messages.
    *   When committing create a `commit.msg` file that contains the commit message.  Then use ```git commit -F commit.msg && rm commit.msg``` to commit the changes.

## 4. Internal Modules & Specific Requirements

*   **Datastore Module:**
    *   Separate package.
    *   Uses **SQLite3** for all DB operations.
    *   **No ORM**; direct database queries.
    *   DB connection details from environment variables (`.env` file): `DB_PATH`, `DB_NAME`, `DB_PORT`, `DB_USER`, `DB_PASS`.
    *   Ensures `DB_PATH` exists, creates if necessary.
    *   All exposed IDs are integer IDs.
    *   Must support **Entity Definition Discovery** from external libraries (registering entity definitions, automatic table creation, DAO generation).
*   **Multi-tenant Management:** Handles accounts, account users, roles. Users belong to an account. User records include username, hashed password, reset token, token timestamp. Registers permissions with Authorization System.
*   **Payment Gateway Wrapper:** Consistent interface for payment gateways.
    *   Includes **Stripe adapter** (utilizes Stripe API, handles webhook events).
*   **Subscription Management:**
    *   **Tier/Feature/Limit Management:** Defines subscription tiers, features, and limits.
        *   **Limits:** `key`, `name`, `description`, `default_value`. Applied to tiers.
        *   **Features:** `key`, `name`, `description`, list of `permissions` (keys).
        *   **Tiers:** `key`, `status` (`active:public`, `active:private`, `draft`, `deactivated`), `name`, `description`, `monthly_cost`, `yearly_cost`, `features` (list of feature keys), `limits` (dict `limit_key: value`).
        *   Tier creation: DB record + corresponding Stripe product.
        *   Tier removal: Only if deactivated.
        *   Tier deactivation: Only if no active associated accounts.
    *   **Subscription Management:** Handles individual subscriptions.
        *   Triggered by Stripe Webhook `checkout.session.completed`.
        *   Creates DB subscription record.
        *   Creates account and default user (if not exists), links account to subscription/tier.
*   **Authorization System:** Manages user permissions and access control (hybrid RBAC). Provides mechanism for other modules to register permissions.
*   **Templating System:** For dynamic content generation (presentation layer).
*   **Dynamic Form Definitions:** For defining and rendering dynamic forms, based on **Form.io JavaScript SDK** (not hosted/API-based).
*   **Workflow Management Library:** BPM-style library for multi-step workflows. Steps have triggers/actions (e.g., calculate, notify, email).
*   **Web Service:** Central entry point, presentation layer (UI/APIs), interacts with all underlying functionality.

## 5. Non-Functional Requirements

*   **Scalability:** Horizontal scaling for increasing libraries and workflow volume.
*   **Reliability:** Resilient; failure of one external library should not cause orchestrator failure.
*   **Security:** Robust authentication and authorization model.
*   **Performance:** Minimal latency from orchestration layer; optimized communication with external libraries.
*   **Maintainability:** Modular design, clear separation of concerns.
*   **Observability:** Logging and monitoring for workflow execution, success rates, and errors.
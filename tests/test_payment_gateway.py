import os
from unittest.mock import patch, MagicMock, Mock

import pytest

from saas_foundation.payment_gateway.stripe_adapter import StripeAdapter
from saas_foundation.payment_gateway.manager import PaymentGatewayManager


# Mock environment variables for Stripe
@pytest.fixture
def mock_stripe_env_vars():
    with patch.dict(
        os.environ,
        {
            "STRIPE_SECRET_KEY": "test_secret_key",
            "STRIPE_WEBHOOK_SECRET": "test_webhook_secret",
        },
    ):
        yield


@pytest.fixture(autouse=True)
def mock_stripe_env_vars_unconfigured():
    with patch.dict(
        os.environ,
        {
            "STRIPE_SECRET_KEY": "",
            "STRIPE_WEBHOOK_SECRET": "",
        },
    ):
        yield


@pytest.fixture
def mock_logger():
    return Mock()


# Fixture for StripeAdapter with mocked stripe API
@pytest.fixture
def mock_stripe_adapter(mock_logger, mock_stripe_env_vars):
    with patch("stripe.Charge.create") as mock_charge_create:
        with patch("stripe.Webhook.construct_event") as mock_webhook_construct_event:
            with patch("stripe.Customer.create") as mock_customer_create:
                with patch("stripe.PaymentMethod.attach") as mock_payment_method_attach:
                    with patch("stripe.PaymentMethod.list") as mock_payment_method_list:
                        with patch(
                            "stripe.Subscription.create"
                        ) as mock_subscription_create:
                            with patch(
                                "stripe.Subscription.delete"
                            ) as mock_subscription_delete:
                                with patch(
                                    "stripe.Product.create"
                                ) as mock_product_create:
                                    with patch(
                                        "stripe.Product.retrieve"
                                    ) as mock_product_retrieve:
                                        with patch(
                                            "stripe.Product.modify"
                                        ) as mock_product_modify:

                                            adapter = StripeAdapter(mock_logger)
                                            adapter.mock_charge_create = (
                                                mock_charge_create
                                            )
                                            adapter.mock_webhook_construct_event = (
                                                mock_webhook_construct_event
                                            )
                                            adapter.mock_customer_create = (
                                                mock_customer_create
                                            )
                                            adapter.mock_payment_method_attach = (
                                                mock_payment_method_attach
                                            )
                                            adapter.mock_payment_method_list = (
                                                mock_payment_method_list
                                            )
                                            adapter.mock_subscription_create = (
                                                mock_subscription_create
                                            )
                                            adapter.mock_subscription_delete = (
                                                mock_subscription_delete
                                            )
                                            adapter.mock_product_create = (
                                                mock_product_create
                                            )
                                            adapter.mock_product_retrieve = (
                                                mock_product_retrieve
                                            )
                                            adapter.mock_product_modify = (
                                                mock_product_modify
                                            )
                                            yield adapter


# Fixture for PaymentGatewayManager
@pytest.fixture
def payment_gateway_manager(mock_logger):
    return PaymentGatewayManager(mock_logger)


def test_stripe_adapter_process_payment(mock_stripe_adapter):
    mock_stripe_adapter.mock_charge_create.return_value = MagicMock(
        to_dict=lambda: {"id": "ch_123", "amount": 1000}
    )
    result = mock_stripe_adapter.process_payment(
        10.00, "usd", "tok_123", "Test Payment"
    )
    assert result["id"] == "ch_123"
    mock_stripe_adapter.mock_charge_create.assert_called_once_with(
        amount=1000, currency="usd", source="tok_123", description="Test Payment"
    )


def test_stripe_adapter_handle_webhook(mock_stripe_adapter):
    mock_stripe_adapter.mock_webhook_construct_event.return_value = MagicMock(
        to_dict=lambda: {"type": "payment_intent.succeeded"}
    )
    result = mock_stripe_adapter.handle_webhook("payload", "signature")
    assert result["type"] == "payment_intent.succeeded"
    mock_stripe_adapter.mock_webhook_construct_event.assert_called_once_with(
        "payload", "signature", "test_webhook_secret"
    )


def test_stripe_adapter_create_customer(mock_stripe_adapter):
    mock_stripe_adapter.mock_customer_create.return_value = MagicMock(
        to_dict=lambda: {"id": "cus_123", "email": "test@example.com"}
    )
    result = mock_stripe_adapter.create_customer("test@example.com", "Test Customer")
    assert result["id"] == "cus_123"
    mock_stripe_adapter.mock_customer_create.assert_called_once_with(
        email="test@example.com", description="Test Customer"
    )


def test_stripe_adapter_create_payment_method(mock_stripe_adapter):
    mock_stripe_adapter.mock_payment_method_attach.return_value = MagicMock(
        to_dict=lambda: {"id": "pm_123"}
    )
    result = mock_stripe_adapter.create_payment_method("cus_123", "pm_token_123")
    assert result["id"] == "pm_123"
    mock_stripe_adapter.mock_payment_method_attach.assert_called_once_with(
        "pm_token_123", customer="cus_123"
    )


def test_stripe_adapter_attach_payment_method_to_customer(mock_stripe_adapter):
    mock_stripe_adapter.mock_payment_method_attach.return_value = MagicMock(
        to_dict=lambda: {"id": "pm_attached_123"}
    )
    result = mock_stripe_adapter.attach_payment_method_to_customer("cus_123", "pm_123")
    assert result["id"] == "pm_attached_123"
    mock_stripe_adapter.mock_payment_method_attach.assert_called_once_with(
        "pm_123", customer="cus_123"
    )


def test_stripe_adapter_get_customer_payment_methods(mock_stripe_adapter):
    mock_stripe_adapter.mock_payment_method_list.return_value = MagicMock(
        data=[MagicMock(to_dict=lambda: {"id": "pm_1", "type": "card"})]
    )
    result = mock_stripe_adapter.get_customer_payment_methods("cus_123")
    assert len(result) == 1
    assert result[0]["id"] == "pm_1"
    mock_stripe_adapter.mock_payment_method_list.assert_called_once_with(
        customer="cus_123", type="card"
    )


def test_stripe_adapter_create_subscription(mock_stripe_adapter):
    mock_stripe_adapter.mock_subscription_create.return_value = MagicMock(
        to_dict=lambda: {"id": "sub_123"}
    )
    result = mock_stripe_adapter.create_subscription("cus_123", "price_123")
    assert result["id"] == "sub_123"
    mock_stripe_adapter.mock_subscription_create.assert_called_once_with(
        customer="cus_123",
        items=[
            {"price": "price_123"},
        ],
        expand=["latest_invoice.payment_intent"],
    )


def test_stripe_adapter_cancel_subscription(mock_stripe_adapter):
    mock_stripe_adapter.mock_subscription_delete.return_value = MagicMock(
        to_dict=lambda: {"id": "sub_canceled_123"}
    )
    result = mock_stripe_adapter.cancel_subscription("sub_123")
    assert result["id"] == "sub_canceled_123"
    mock_stripe_adapter.mock_subscription_delete.assert_called_once_with("sub_123")


def test_payment_gateway_manager_get_adapter(payment_gateway_manager):
    adapter = payment_gateway_manager.get_adapter("stripe")
    assert isinstance(adapter, StripeAdapter)


def test_payment_gateway_manager_get_adapter_not_found(payment_gateway_manager):
    with pytest.raises(
        ValueError, match="Payment gateway adapter 'non_existent' not found."
    ):
        payment_gateway_manager.get_adapter("non_existent")


def test_payment_gateway_manager_stripe_property(payment_gateway_manager):
    adapter = payment_gateway_manager.stripe
    assert isinstance(adapter, StripeAdapter)


def test_stripe_adapter_create_product(mock_stripe_adapter):
    mock_stripe_adapter.mock_product_create.return_value = MagicMock(
        to_dict=lambda: {"id": "prod_123", "name": "Test Product"}
    )
    result = mock_stripe_adapter.create_product(
        "Test Product", "A test product description", "prod_123"
    )
    assert result["id"] == "prod_123"
    assert result["name"] == "Test Product"
    mock_stripe_adapter.mock_product_create.assert_called_once_with(
        name="Test Product", description="A test product description", id="prod_123"
    )


def test_stripe_adapter_retrieve_product(mock_stripe_adapter):
    mock_stripe_adapter.mock_product_retrieve.return_value = MagicMock(
        to_dict=lambda: {"id": "prod_123", "name": "Retrieved Product"}
    )
    result = mock_stripe_adapter.retrieve_product("prod_123")
    assert result["id"] == "prod_123"
    assert result["name"] == "Retrieved Product"
    mock_stripe_adapter.mock_product_retrieve.assert_called_once_with("prod_123")


def test_stripe_adapter_update_product(mock_stripe_adapter):
    mock_stripe_adapter.mock_product_modify.return_value = MagicMock(
        to_dict=lambda: {"id": "prod_123", "name": "Updated Product", "active": True}
    )
    result = mock_stripe_adapter.update_product(
        "prod_123", name="Updated Product", active=True
    )
    assert result["id"] == "prod_123"
    assert result["name"] == "Updated Product"
    assert result["active"] is True
    mock_stripe_adapter.mock_product_modify.assert_called_once_with(
        "prod_123", name="Updated Product", active=True
    )


def test_stripe_adapter_archive_product(mock_stripe_adapter):
    mock_stripe_adapter.mock_product_modify.return_value = MagicMock(
        to_dict=lambda: {"id": "prod_123", "active": False}
    )
    result = mock_stripe_adapter.archive_product("prod_123")
    assert result["id"] == "prod_123"
    assert result["active"] is False
    mock_stripe_adapter.mock_product_modify.assert_called_once_with(
        "prod_123", active=False
    )


# Mock Mode Tests
@pytest.fixture
def mock_stripe_adapter_unconfigured(mock_logger, mock_stripe_env_vars_unconfigured):
    # We don't need to patch stripe API calls here, as they should not be called in mock mode
    adapter = StripeAdapter(mock_logger)
    yield adapter


def test_stripe_adapter_mock_mode_create_product(mock_stripe_adapter_unconfigured):
    adapter = mock_stripe_adapter_unconfigured
    mock_product_name = "Mock Product Name"
    mock_product_description = "Mock Product Description"
    mock_product_id = "prod_mock_test"

    with patch("stripe.Product.create") as mock_stripe_create:
        result = adapter.create_product(
            mock_product_name, mock_product_description, mock_product_id
        )
        mock_stripe_create.assert_not_called()
        adapter.logger.info.assert_called_with(
            f"Mocking create_product for name: {mock_product_name}"
        )
        assert result["name"] == mock_product_name
        assert result["description"] == mock_product_description
        assert result["id"] == mock_product_id
        assert result["object"] == "product"
        assert result["active"] is True
        assert result["livemode"] is False


def test_stripe_adapter_mock_mode_retrieve_product(mock_stripe_adapter_unconfigured):
    adapter = mock_stripe_adapter_unconfigured
    mock_product_id = "prod_mock_retrieve"

    with patch("stripe.Product.retrieve") as mock_stripe_retrieve:
        result = adapter.retrieve_product(mock_product_id)
        mock_stripe_retrieve.assert_not_called()
        adapter.logger.info.assert_called_with(
            f"Mocking retrieve_product for product_id: {mock_product_id}"
        )
        assert result["id"] == mock_product_id
        assert result["name"] == f"Mock Product {mock_product_id}"
        assert result["object"] == "product"
        assert result["active"] is True
        assert result["livemode"] is False


def test_stripe_adapter_mock_mode_update_product(mock_stripe_adapter_unconfigured):
    adapter = mock_stripe_adapter_unconfigured
    mock_product_id = "prod_mock_update"
    updated_name = "Updated Mock Product"
    updated_description = "Updated Mock Description"
    updated_active = False

    with patch("stripe.Product.modify") as mock_stripe_modify:
        result = adapter.update_product(
            mock_product_id,
            name=updated_name,
            description=updated_description,
            active=updated_active,
        )
        mock_stripe_modify.assert_not_called()
        adapter.logger.info.assert_called_with(
            f"Mocking update_product for product_id: {mock_product_id}"
        )
        assert result["id"] == mock_product_id
        assert result["name"] == updated_name
        assert result["description"] == updated_description
        assert result["active"] is updated_active
        assert result["object"] == "product"
        assert result["livemode"] is False


def test_stripe_adapter_mock_mode_archive_product(mock_stripe_adapter_unconfigured):
    adapter = mock_stripe_adapter_unconfigured
    mock_product_id = "prod_mock_archive"

    with patch("stripe.Product.modify") as mock_stripe_modify:
        result = adapter.archive_product(mock_product_id)
        mock_stripe_modify.assert_not_called()
        adapter.logger.info.assert_called_with(
            f"Mocking archive_product for product_id: {mock_product_id}"
        )
        assert result["id"] == mock_product_id
        assert result["active"] is False
        assert result["object"] == "product"
        assert result["livemode"] is False

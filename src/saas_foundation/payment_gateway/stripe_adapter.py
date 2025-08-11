import os
from typing import Any

import stripe

from saas_foundation.payment_gateway.base import PaymentGatewayAdapter


class StripeAdapter(PaymentGatewayAdapter):
    def __init__(self, logger: Any):
        self.logger = logger
        self._mock_mode = False

        stripe_secret_key = os.getenv("STRIPE_SECRET_KEY")
        stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

        if not stripe_secret_key or not stripe_webhook_secret:
            self.logger.warning(
                "Stripe API keys not fully configured. Operating in mock mode. "
                "Set STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET for live operations."
            )
            self._mock_mode = True
            self.webhook_secret = ""  # Initialize webhook_secret even in mock mode
        else:
            stripe.api_key = stripe_secret_key
            self.webhook_secret = stripe_webhook_secret
            self.logger.info("Stripe adapter initialized for live operations.")

    def process_payment(
        self, amount: float, currency: str, token: str, description: str
    ) -> dict:
        try:
            charge = stripe.Charge.create(
                amount=int(amount * 100),  # Stripe expects amount in cents
                currency=currency,
                source=token,  # obtained with Stripe.js
                description=description,
            )
            return charge.to_dict()
        except stripe.error.CardError as e:
            self.logger.error(f"Card declined: {e.user_message}")
            raise ValueError(f"Card declined: {e.user_message}") from e
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error processing payment: {e}")
            raise ValueError(f"Stripe error: {e}") from e

    def handle_webhook(self, payload: dict, signature: str) -> dict:
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            # Process the event

            # In a real application, you would have a dispatcher here
            # to handle different event types (e.g., checkout.session.completed)
            return event.to_dict()
        except ValueError as e:
            self.logger.error(f"Invalid payload: {e}")
            raise ValueError(f"Invalid payload: {e}") from e
        except stripe.error.SignatureVerificationError as e:
            self.logger.error(f"Invalid signature: {e}")
            raise ValueError(f"Invalid signature: {e}") from e

    def create_customer(self, email: str, description: str = None) -> dict:
        try:
            customer = stripe.Customer.create(email=email, description=description)
            return customer.to_dict()
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error creating customer: {e}")
            raise ValueError(f"Stripe error creating customer: {e}") from e

    def create_payment_method(self, customer_id: str, token: str) -> dict:
        # In Stripe, you usually attach a PaymentMethod to a Customer
        # This method might be more about creating a PaymentMethod from a token/source
        # and then attaching it. For simplicity, let's assume token is a PaymentMethod ID
        # or a source that can be attached.
        try:
            # If token is a card token, you might need to create a PaymentMethod first
            # For now, assuming token is a PaymentMethod ID or a source that can be attached
            payment_method = stripe.PaymentMethod.attach(
                token,  # This should be a PaymentMethod ID, not a card token
                customer=customer_id,
            )
            return payment_method.to_dict()
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error creating payment method: {e}")
            raise ValueError(f"Stripe error creating payment method: {e}") from e

    def attach_payment_method_to_customer(
        self, customer_id: str, payment_method_id: str
    ) -> dict:
        try:
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id,
            )
            return payment_method.to_dict()
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error attaching payment method: {e}")
            raise ValueError(f"Stripe error attaching payment method: {e}") from e

    def get_customer_payment_methods(self, customer_id: str) -> list[dict]:
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id, type="card"  # or other types
            )
            return [pm.to_dict() for pm in payment_methods.data]
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error getting payment methods: {e}")
            raise ValueError(f"Stripe error getting payment methods: {e}") from e

    def create_subscription(self, customer_id: str, price_id: str) -> dict:
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[
                    {"price": price_id},
                ],
                expand=["latest_invoice.payment_intent"],
            )
            return subscription.to_dict()
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error creating subscription: {e}")
            raise ValueError(f"Stripe error creating subscription: {e}") from e

    def cancel_subscription(self, subscription_id: str) -> dict:
        try:
            canceled_subscription = stripe.Subscription.delete(subscription_id)
            return canceled_subscription.to_dict()
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error canceling subscription: {e}")
            raise ValueError(f"Stripe error canceling subscription: {e}") from e

    def create_product(
        self, name: str, description: str = None, product_id: str = None
    ) -> dict:
        if self._mock_mode:
            self.logger.info(f"Mocking create_product for name: {name}")
            mock_id = (
                product_id
                if product_id
                else f"prod_mock_{name.lower().replace(' ', '_')}"
            )
            return {
                "id": mock_id,
                "object": "product",
                "active": True,
                "created": 1678886400,  # Example timestamp
                "description": description,
                "livemode": False,
                "name": name,
                "package_dimensions": None,
                "shippable": None,
                "statement_descriptor": None,
                "unit_label": None,
                "updated": 1678886400,
                "url": None,
                "metadata": {},
            }
        try:
            product_data = {
                "name": name,
            }
            if description:
                product_data["description"] = description
            if product_id:
                product_data["id"] = product_id  # Allows setting a custom product ID

            product = stripe.Product.create(**product_data)
            return product.to_dict()
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error creating product: {e}")
            raise ValueError(f"Stripe error creating product: {e}") from e

    def retrieve_product(self, product_id: str) -> dict:
        if self._mock_mode:
            self.logger.info(f"Mocking retrieve_product for product_id: {product_id}")
            return {
                "id": product_id,
                "object": "product",
                "active": True,
                "created": 1678886400,
                "description": "Mock product description",
                "livemode": False,
                "name": f"Mock Product {product_id}",
                "package_dimensions": None,
                "shippable": None,
                "statement_descriptor": None,
                "unit_label": None,
                "updated": 1678886400,
                "url": None,
                "metadata": {},
            }
        try:
            product = stripe.Product.retrieve(product_id)
            return product.to_dict()
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error retrieving product: {e}")
            raise ValueError(f"Stripe error retrieving product: {e}") from e

    def update_product(
        self,
        product_id: str,
        name: str = None,
        description: str = None,
        active: bool = None,
    ) -> dict:
        if self._mock_mode:
            self.logger.info(f"Mocking update_product for product_id: {product_id}")
            mock_product = {
                "id": product_id,
                "object": "product",
                "active": True if active is None else active,
                "created": 1678886400,
                "description": (
                    description if description else "Mock product description"
                ),
                "livemode": False,
                "name": name if name else f"Mock Product {product_id}",
                "package_dimensions": None,
                "shippable": None,
                "statement_descriptor": None,
                "unit_label": None,
                "updated": 1678886400,
                "url": None,
                "metadata": {},
            }
            return mock_product
        try:
            update_data = {}
            if name:
                update_data["name"] = name
            if description:
                update_data["description"] = description
            if active is not None:
                update_data["active"] = active

            product = stripe.Product.modify(product_id, **update_data)
            return product.to_dict()
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error updating product: {e}")
            raise ValueError(f"Stripe error updating product: {e}") from e

    def archive_product(self, product_id: str) -> dict:
        if self._mock_mode:
            self.logger.info(f"Mocking archive_product for product_id: {product_id}")
            return {
                "id": product_id,
                "object": "product",
                "active": False,
                "created": 1678886400,
                "description": "Mock product description",
                "livemode": False,
                "name": f"Mock Product {product_id}",
                "package_dimensions": None,
                "shippable": None,
                "statement_descriptor": None,
                "unit_label": None,
                "updated": 1678886400,
                "url": None,
                "metadata": {},
            }
        try:
            # Archiving a product in Stripe is done by setting its 'active' status to False
            product = stripe.Product.modify(product_id, active=False)
            return product.to_dict()
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error archiving product: {e}")
            raise ValueError(f"Stripe error archiving product: {e}") from e

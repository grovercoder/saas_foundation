import stripe
import os
from saas_foundation.payment_gateway.base import PaymentGatewayAdapter
from typing import Any

class StripeAdapter(PaymentGatewayAdapter):
    def __init__(self, logger: Any):
        self.logger = logger
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not stripe.api_key:
            self.logger.error("STRIPE_SECRET_KEY environment variable not set.")
            raise ValueError("STRIPE_SECRET_KEY environment variable not set.")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if not self.webhook_secret:
            self.logger.error("STRIPE_WEBHOOK_SECRET environment variable not set.")
            raise ValueError("STRIPE_WEBHOOK_SECRET environment variable not set.")

    def process_payment(self, amount: float, currency: str, token: str, description: str) -> dict:
        try:
            charge = stripe.Charge.create(
                amount=int(amount * 100),  # Stripe expects amount in cents
                currency=currency,
                source=token,  # obtained with Stripe.js
                description=description
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
                payload,
                signature,
                self.webhook_secret
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
            customer = stripe.Customer.create(
                email=email,
                description=description
            )
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
                token, # This should be a PaymentMethod ID, not a card token
                customer=customer_id,
            )
            return payment_method.to_dict()
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe error creating payment method: {e}")
            raise ValueError(f"Stripe error creating payment method: {e}") from e

    def attach_payment_method_to_customer(self, customer_id: str, payment_method_id: str) -> dict:
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
                customer=customer_id,
                type="card" # or other types
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

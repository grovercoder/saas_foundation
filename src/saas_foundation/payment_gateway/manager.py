from typing import Any

from saas_foundation.payment_gateway.base import PaymentGatewayAdapter
from saas_foundation.payment_gateway.stripe_adapter import StripeAdapter


class PaymentGatewayManager:
    def __init__(self, logger: Any, adapters: dict | None = None):
        self.logger = logger
        if adapters is None:
            self._adapters = {
                "stripe": StripeAdapter(self.logger)  # Initialize with StripeAdapter
            }
        else:
            self._adapters = adapters

    def get_adapter(self, name: str) -> PaymentGatewayAdapter:
        adapter = self._adapters.get(name)
        if not adapter:
            raise ValueError(f"Payment gateway adapter '{name}' not found.")
        return adapter

    @property
    def stripe(self) -> StripeAdapter:
        return self.get_adapter("stripe")

    def create_product(
        self, name: str, description: str = None, product_id: str = None
    ) -> dict:
        return self.stripe.create_product(name, description, product_id)

    def retrieve_product(self, product_id: str) -> dict:
        return self.stripe.retrieve_product(product_id)

    def update_product(
        self,
        product_id: str,
        name: str = None,
        description: str = None,
        active: bool = None,
    ) -> dict:
        return self.stripe.update_product(product_id, name, description, active)

    def archive_product(self, product_id: str) -> dict:
        return self.stripe.archive_product(product_id)

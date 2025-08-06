from saas_foundation.payment_gateway.base import PaymentGatewayAdapter
from saas_foundation.payment_gateway.stripe_adapter import StripeAdapter
from typing import Any

class PaymentGatewayManager:
    def __init__(self, logger: Any, adapters: dict | None = None):
        self.logger = logger
        if adapters is None:
            self._adapters = {
                "stripe": StripeAdapter(self.logger) # Initialize with StripeAdapter
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

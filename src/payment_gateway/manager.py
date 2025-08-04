from src.payment_gateway.base import PaymentGatewayAdapter
from src.payment_gateway.stripe_adapter import StripeAdapter

class PaymentGatewayManager:
    def __init__(self, adapters: dict | None = None):
        if adapters is None:
            self._adapters = {
                "stripe": StripeAdapter() # Initialize with StripeAdapter
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

from abc import ABC, abstractmethod


class PaymentGatewayAdapter(ABC):
    @abstractmethod
    def process_payment(
        self, amount: float, currency: str, token: str, description: str
    ) -> dict:
        pass

    @abstractmethod
    def handle_webhook(self, payload: dict, signature: str) -> dict:
        pass

    @abstractmethod
    def create_customer(self, email: str, description: str = None) -> dict:
        pass

    @abstractmethod
    def create_payment_method(self, customer_id: str, token: str) -> dict:
        pass

    @abstractmethod
    def attach_payment_method_to_customer(
        self, customer_id: str, payment_method_id: str
    ) -> dict:
        pass

    @abstractmethod
    def get_customer_payment_methods(self, customer_id: str) -> list[dict]:
        pass

    @abstractmethod
    def create_subscription(self, customer_id: str, price_id: str) -> dict:
        pass

    @abstractmethod
    def cancel_subscription(self, subscription_id: str) -> dict:
        pass

from dataclasses import dataclass
from decimal import Decimal
import uuid


@dataclass(frozen=True)
class PaymentResult:
    approved: bool
    status: str
    reference: str = ""
    message: str = ""


class BasePaymentService:
    def authorize(self, *, amount: Decimal, method: str, order_reference: str) -> PaymentResult:
        raise NotImplementedError


class MockPaymentService(BasePaymentService):
    """
    Servicio mock seguro.
    Permite flujo realista de aprobación/rechazo sin credenciales externas.
    """

    def authorize(self, *, amount: Decimal, method: str, order_reference: str) -> PaymentResult:
        if amount <= 0:
            return PaymentResult(
                approved=False,
                status="rejected",
                message="Monto inválido para pago.",
            )

        if method == "cash_on_delivery":
            return PaymentResult(
                approved=True,
                status="pending_settlement",
                reference=f"COD-{uuid.uuid4().hex[:10].upper()}",
                message="Pago contra entrega registrado.",
            )

        return PaymentResult(
            approved=True,
            status="approved",
            reference=f"MOCK-{uuid.uuid4().hex[:12].upper()}",
            message=f"Pago mock aprobado para {order_reference}.",
        )


def get_payment_service() -> BasePaymentService:
    return MockPaymentService()

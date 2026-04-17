import shutil
import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Pedido, Producto


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PurchaseFlowTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(
            username="cliente1",
            email="cliente1@example.com",
            password="ComplexPass123",
        )
        self.product = Producto.objects.create(
            nombre="Whisky Test",
            descripcion="Botella de prueba",
            precio=Decimal("25000"),
            stock=5,
            activo=True,
        )

    def test_checkout_creates_order_with_tracking_and_qr(self):
        self.client.login(username="cliente1", password="ComplexPass123")

        add_response = self.client.post(
            reverse("cart_add", kwargs={"product_id": self.product.id}),
            {"quantity": 2},
        )
        self.assertEqual(add_response.status_code, 302)

        checkout_response = self.client.post(
            reverse("checkout"),
            {
                "tipo_entrega": Pedido.TipoEntrega.RETIRO,
                "metodo_pago": Pedido.MetodoPago.MOCK_CARD,
            },
        )
        self.assertEqual(checkout_response.status_code, 302)

        order = Pedido.objects.get(usuario=self.user)
        self.assertTrue(order.tracking_token)
        self.assertEqual(order.estado_pago, Pedido.EstadoPago.APROBADO)
        self.assertTrue(order.referencia_pago.startswith("MOCK-"))
        self.assertIsNotNone(order.qr_code)
        self.assertEqual(order.detalles.count(), 1)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(self.product.contador_ventas, 2)

    def test_tracking_endpoint_works_with_token(self):
        order = Pedido.objects.create(
            usuario=self.user,
            total=Decimal("1000.00"),
        )

        response = self.client.get(reverse("order_tracking", kwargs={"token": order.tracking_token}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, order.tracking_token)

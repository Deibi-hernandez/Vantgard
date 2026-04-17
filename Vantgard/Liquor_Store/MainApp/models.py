import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


def build_unique_slug(instance, source_value, slug_field="slug"):
    base_slug = slugify(source_value) or "item"
    slug = base_slug
    model_class = instance.__class__
    counter = 2

    while model_class.objects.filter(**{slug_field: slug}).exclude(pk=instance.pk).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrador"
        CLIENTE = "cliente", "Cliente"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENTE)

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return self.get_full_name() or self.username


class Producto(models.Model):
    nombre = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    descripcion = models.TextField()
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    volumen = models.CharField(max_length=50, blank=True)
    stock = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True)
    contador_ventas = models.PositiveIntegerField(default=0, editable=False)
    is_offer = models.BooleanField(default=False)
    discount_percent = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    is_limited_edition = models.BooleanField(default=False)
    countdown_end = models.DateTimeField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "producto"
        verbose_name_plural = "productos"

    def __str__(self):
        return self.nombre

    def clean(self):
        if self.discount_percent and not self.is_offer:
            raise ValidationError(
                {"discount_percent": "Marca el producto como oferta para aplicar descuento."}
            )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(self, self.nombre)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"slug": self.slug})

    def precio_final(self):
        if not self.is_offer or self.discount_percent == 0:
            return self.precio

        discount = (self.precio * Decimal(self.discount_percent)) / Decimal("100")
        return (self.precio - discount).quantize(Decimal("0.01"))


class GiftExperience(models.Model):
    class TipoEmpaque(models.TextChoices):
        ELEGANTE = "elegante", "Elegante"
        PREMIUM = "premium", "Premium"
        COLECCION = "coleccion", "Coleccion"

    mensaje_personalizado = models.TextField(blank=True)
    tipo_empaque = models.CharField(
        max_length=30,
        choices=TipoEmpaque.choices,
        default=TipoEmpaque.ELEGANTE,
    )
    costo_extra = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        verbose_name = "gift experience"
        verbose_name_plural = "gift experiences"

    def __str__(self):
        return self.get_tipo_empaque_display()


class Pedido(models.Model):
    class EstadoPedido(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        PAGADO = "pagado", "Pagado"
        PREPARANDO = "preparando", "Preparando"
        ENVIADO = "enviado", "Enviado"
        ENTREGADO = "entregado", "Entregado"
        CANCELADO = "cancelado", "Cancelado"

    class TipoEntrega(models.TextChoices):
        RETIRO = "retiro", "Retiro en tienda"
        ENVIO_LOCAL = "envio_local", "Envio local"
        ENVIO_EXPRESS = "envio_express", "Envio Express 90 min"

    codigo = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="pedidos",
        blank=True,
        null=True,
    )
    estado_pedido = models.CharField(
        max_length=20,
        choices=EstadoPedido.choices,
        default=EstadoPedido.PENDIENTE,
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    qr_code = models.ImageField(upload_to="pedidos/qr/", blank=True, null=True)
    gift_experience = models.OneToOneField(
        GiftExperience,
        on_delete=models.SET_NULL,
        related_name="pedido",
        blank=True,
        null=True,
    )
    tipo_entrega = models.CharField(
        max_length=20,
        choices=TipoEntrega.choices,
        default=TipoEntrega.RETIRO,
    )
    direccion = models.CharField(max_length=255, blank=True)
    comuna = models.CharField(max_length=80, blank=True)
    sector = models.CharField(max_length=80, blank=True)
    es_envio_express = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"

    def __str__(self):
        return f"Pedido {self.codigo}"


class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="detalles_pedido")
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    discount_percent = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["pedido", "producto"],
                name="unique_producto_por_pedido",
            )
        ]
        verbose_name = "detalle de pedido"
        verbose_name_plural = "detalles de pedido"

    def __str__(self):
        return f"{self.cantidad} x {self.producto}"

    def subtotal(self):
        return (self.precio_unitario * self.cantidad).quantize(Decimal("0.01"))


class Blog(models.Model):
    titulo = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    contenido = models.TextField()
    imagen = models.ImageField(upload_to="blog/", blank=True, null=True)
    publicado = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "nota de cata"
        verbose_name_plural = "notas de cata"

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(self, self.titulo)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog_detail", kwargs={"slug": self.slug})

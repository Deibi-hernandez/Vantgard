from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from django.utils.html import format_html

from .forms import ProductoForm
from .models import Blog, CategoriaProducto, CustomUser, DetallePedido, GiftExperience, Pedido, Producto


@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug", "activa", "created_at")
    list_filter = ("activa", "created_at")
    search_fields = ("nombre", "slug")
    prepopulated_fields = {"slug": ("nombre",)}
    readonly_fields = ("created_at",)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_staff",
        "is_superuser",
        "is_active",
    )
    list_filter = ("role", "is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)
    fieldsets = UserAdmin.fieldsets + (
        ("Vantgard", {"fields": ("role",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Vantgard", {"fields": ("role",)}),
    )


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    form = ProductoForm
    list_display = (
        "nombre",
        "categoria",
        "precio",
        "precio_final_display",
        "stock",
        "stock_status",
        "is_offer",
        "discount_percent",
        "is_limited_edition",
        "activo",
    )
    list_filter = ("categoria", "activo", "is_offer", "is_limited_edition", "created_at")
    search_fields = ("nombre", "descripcion", "slug")
    prepopulated_fields = {"slug": ("nombre",)}
    readonly_fields = ("contador_ventas", "created_at", "updated_at")
    list_editable = ("stock", "activo", "is_offer")
    date_hierarchy = "created_at"
    actions = ("mark_as_inactive",)

    @admin.display(description="Precio final")
    def precio_final_display(self, obj):
        return obj.precio_final()

    @admin.display(description="Stock")
    def stock_status(self, obj):
        if obj.stock == 0:
            return "Agotado"
        if obj.stock < 3:
            return "Critico"
        return "Disponible"

    @admin.action(description="Desactivar productos seleccionados")
    def mark_as_inactive(self, request, queryset):
        queryset.update(activo=False)


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0
    autocomplete_fields = ("producto",)
    readonly_fields = ("subtotal_display", "created_at")
    fields = (
        "producto",
        "cantidad",
        "precio_unitario",
        "discount_percent",
        "subtotal_display",
        "created_at",
    )

    @admin.display(description="Subtotal")
    def subtotal_display(self, obj):
        if not obj.pk:
            return "-"
        return obj.subtotal()


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "tracking_token",
        "usuario",
        "estado_pedido",
        "estado_pago",
        "metodo_pago",
        "tipo_entrega",
        "es_envio_express",
        "total",
        "detalles_count",
        "created_at",
    )
    list_filter = ("estado_pedido", "estado_pago", "metodo_pago", "tipo_entrega", "es_envio_express", "created_at")
    search_fields = (
        "codigo",
        "tracking_token",
        "usuario__username",
        "usuario__email",
        "direccion",
        "comuna",
        "sector",
        "referencia_pago",
    )
    autocomplete_fields = ("usuario", "gift_experience")
    readonly_fields = ("codigo", "tracking_token", "created_at", "updated_at", "qr_preview")
    inlines = (DetallePedidoInline,)
    date_hierarchy = "created_at"
    actions = (
        "mark_as_preparando",
        "mark_as_en_camino",
        "mark_as_listo_retiro",
        "mark_as_entregado",
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            details_total=Count("detalles"),
        )

    @admin.display(description="Items")
    def detalles_count(self, obj):
        return obj.details_total

    @admin.display(description="QR")
    def qr_preview(self, obj):
        if not obj.qr_code:
            return "-"
        return format_html('<img src="{}" width="90" height="90" alt="QR pedido">', obj.qr_code.url)

    @admin.action(description="Marcar como preparando")
    def mark_as_preparando(self, request, queryset):
        queryset.update(estado_pedido=Pedido.EstadoPedido.PREPARANDO)

    @admin.action(description="Marcar como en camino")
    def mark_as_en_camino(self, request, queryset):
        queryset.update(estado_pedido=Pedido.EstadoPedido.EN_CAMINO)

    @admin.action(description="Marcar como listo para retiro")
    def mark_as_listo_retiro(self, request, queryset):
        queryset.update(estado_pedido=Pedido.EstadoPedido.LISTO_RETIRO)

    @admin.action(description="Marcar como entregado")
    def mark_as_entregado(self, request, queryset):
        queryset.update(estado_pedido=Pedido.EstadoPedido.ENTREGADO)


@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = (
        "pedido",
        "producto",
        "cantidad",
        "precio_unitario",
        "discount_percent",
        "subtotal_display",
        "created_at",
    )
    list_filter = ("created_at", "discount_percent")
    search_fields = ("pedido__codigo", "producto__nombre")
    autocomplete_fields = ("pedido", "producto")
    readonly_fields = ("created_at",)

    @admin.display(description="Subtotal")
    def subtotal_display(self, obj):
        return obj.subtotal()


@admin.register(GiftExperience)
class GiftExperienceAdmin(admin.ModelAdmin):
    list_display = ("tipo_empaque", "costo_extra", "mensaje_preview")
    list_filter = ("tipo_empaque",)
    search_fields = ("mensaje_personalizado", "tipo_empaque")

    @admin.display(description="Mensaje")
    def mensaje_preview(self, obj):
        if not obj.mensaje_personalizado:
            return "-"
        return obj.mensaje_personalizado[:60]


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ("titulo", "publicado", "created_at", "updated_at")
    list_filter = ("publicado", "created_at")
    search_fields = ("titulo", "contenido", "slug")
    prepopulated_fields = {"slug": ("titulo",)}
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"

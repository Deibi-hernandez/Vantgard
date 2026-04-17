from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Blog, CustomUser, DetallePedido, GiftExperience, Pedido, Producto


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
    list_display = (
        "nombre",
        "precio",
        "precio_final_display",
        "stock",
        "stock_status",
        "is_offer",
        "discount_percent",
        "is_limited_edition",
        "activo",
    )
    list_filter = ("activo", "is_offer", "is_limited_edition", "created_at")
    search_fields = ("nombre", "descripcion", "slug")
    prepopulated_fields = {"slug": ("nombre",)}
    readonly_fields = ("contador_ventas", "created_at", "updated_at")
    list_editable = ("stock", "activo", "is_offer")
    date_hierarchy = "created_at"

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
        "usuario",
        "estado_pedido",
        "tipo_entrega",
        "es_envio_express",
        "total",
        "created_at",
    )
    list_filter = ("estado_pedido", "tipo_entrega", "es_envio_express", "created_at")
    search_fields = (
        "codigo",
        "usuario__username",
        "usuario__email",
        "direccion",
        "comuna",
        "sector",
    )
    autocomplete_fields = ("usuario", "gift_experience")
    readonly_fields = ("codigo", "created_at", "updated_at")
    inlines = (DetallePedidoInline,)
    date_hierarchy = "created_at"


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

from decimal import Decimal

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CartAddForm, CartUpdateForm, CheckoutForm, CustomerRegistrationForm
from .models import Blog, DetallePedido, Pedido, Producto
from .services import get_payment_service

CART_SESSION_KEY = "cart_items"


def _get_cart(request):
    return request.session.get(CART_SESSION_KEY, {})


def _save_cart(request, cart):
    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True


def _build_cart_items(cart):
    product_ids = [int(product_id) for product_id in cart.keys()]
    products = Producto.objects.filter(pk__in=product_ids, activo=True)
    products_by_id = {product.id: product for product in products}

    items = []
    total = Decimal("0.00")

    for product_id, quantity in cart.items():
        product = products_by_id.get(int(product_id))
        if not product:
            continue

        qty = int(quantity)
        unit_price = product.precio_final()
        subtotal = (unit_price * qty).quantize(Decimal("0.01"))
        total += subtotal
        items.append(
            {
                "product": product,
                "quantity": qty,
                "unit_price": unit_price,
                "subtotal": subtotal,
            }
        )

    return items, total.quantize(Decimal("0.01"))


def home(request):
    productos_destacados = Producto.objects.filter(activo=True).order_by(
        "-is_limited_edition",
        "-created_at",
    )[:3]
    ofertas = Producto.objects.filter(activo=True, is_offer=True).order_by(
        "-discount_percent",
        "-created_at",
    )[:3]
    mas_comprados = Producto.objects.filter(activo=True).order_by(
        "-contador_ventas",
        "nombre",
    )[:3]
    ultimas_notas = Blog.objects.filter(publicado=True)[:3]

    context = {
        "productos_destacados": productos_destacados,
        "ofertas": ofertas,
        "mas_comprados": mas_comprados,
        "ultimas_notas": ultimas_notas,
    }
    return render(request, "MainApp/home.html", context)


def product_list(request):
    productos = Producto.objects.filter(activo=True).order_by("nombre")
    return render(request, "MainApp/products/list.html", {"productos": productos})


def product_detail(request, slug):
    producto = get_object_or_404(Producto, slug=slug, activo=True)
    relacionados = Producto.objects.filter(activo=True).exclude(pk=producto.pk)[:3]

    return render(
        request,
        "MainApp/products/detail.html",
        {
            "producto": producto,
            "relacionados": relacionados,
        },
    )


def register(request):
    if request.user.is_authenticated:
        return redirect("account")

    if request.method == "POST":
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("account")
    else:
        form = CustomerRegistrationForm()

    return render(request, "MainApp/auth/register.html", {"form": form})


@login_required
def account(request):
    recent_orders = request.user.pedidos.select_related().prefetch_related("detalles__producto")[:5]
    return render(request, "MainApp/account.html", {"recent_orders": recent_orders})


def cart_detail(request):
    cart = _get_cart(request)
    items, total = _build_cart_items(cart)
    update_forms = {item["product"].id: CartUpdateForm(initial={"quantity": item["quantity"]}) for item in items}
    return render(
        request,
        "MainApp/cart/detail.html",
        {
            "items": items,
            "total": total,
            "update_forms": update_forms,
        },
    )


def cart_add(request, product_id):
    if request.method != "POST":
        return redirect("cart_detail")

    product = get_object_or_404(Producto, pk=product_id, activo=True)
    form = CartAddForm(request.POST)

    if not form.is_valid():
        messages.error(request, "Cantidad invalida.")
        return redirect("product_detail", slug=product.slug)

    quantity = form.cleaned_data["quantity"]
    cart = _get_cart(request)
    current_quantity = int(cart.get(str(product.id), 0))
    requested_quantity = current_quantity + quantity

    if requested_quantity > product.stock:
        messages.error(request, "No hay stock suficiente para esa cantidad.")
        return redirect("product_detail", slug=product.slug)

    cart[str(product.id)] = requested_quantity
    _save_cart(request, cart)
    messages.success(request, f"{product.nombre} agregado al carrito.")
    return redirect("cart_detail")


def cart_update(request, product_id):
    if request.method != "POST":
        return redirect("cart_detail")

    product = get_object_or_404(Producto, pk=product_id, activo=True)
    form = CartUpdateForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Cantidad invalida.")
        return redirect("cart_detail")

    quantity = form.cleaned_data["quantity"]
    if quantity > product.stock:
        messages.error(request, "No hay stock suficiente para esa cantidad.")
        return redirect("cart_detail")

    cart = _get_cart(request)
    cart[str(product.id)] = quantity
    _save_cart(request, cart)
    messages.success(request, "Carrito actualizado.")
    return redirect("cart_detail")


def cart_remove(request, product_id):
    if request.method != "POST":
        return redirect("cart_detail")

    cart = _get_cart(request)
    cart.pop(str(product_id), None)
    _save_cart(request, cart)
    messages.success(request, "Producto quitado del carrito.")
    return redirect("cart_detail")


@login_required
def checkout(request):
    cart = _get_cart(request)
    items, total = _build_cart_items(cart)
    if not items:
        messages.info(request, "Tu carrito esta vacio.")
        return redirect("product_list")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                product_ids = [item["product"].id for item in items]
                locked_products = {
                    product.id: product
                    for product in Producto.objects.select_for_update().filter(pk__in=product_ids, activo=True)
                }

                for item in items:
                    locked_product = locked_products.get(item["product"].id)
                    if not locked_product or locked_product.stock < item["quantity"]:
                        messages.error(
                            request,
                            f"Stock insuficiente para {item['product'].nombre}.",
                        )
                        return redirect("cart_detail")

                order = Pedido.objects.create(
                    usuario=request.user,
                    tipo_entrega=form.cleaned_data["tipo_entrega"],
                    metodo_pago=form.cleaned_data["metodo_pago"],
                    direccion=form.cleaned_data.get("direccion", ""),
                    comuna=form.cleaned_data.get("comuna", ""),
                    sector=form.cleaned_data.get("sector", ""),
                    es_envio_express=form.cleaned_data["tipo_entrega"] == Pedido.TipoEntrega.ENVIO_EXPRESS,
                )

                for item in items:
                    product = locked_products[item["product"].id]
                    DetallePedido.objects.create(
                        pedido=order,
                        producto=product,
                        cantidad=item["quantity"],
                        precio_unitario=item["unit_price"],
                        discount_percent=product.discount_percent if product.is_offer else 0,
                    )

                order.recalculate_total(save=True)
                payment_service = get_payment_service()
                payment_result = payment_service.authorize(
                    amount=order.total,
                    method=order.metodo_pago,
                    order_reference=str(order.codigo),
                )

                order.referencia_pago = payment_result.reference
                order.mensaje_pago = payment_result.message

                if payment_result.approved:
                    if payment_result.status == "approved":
                        order.estado_pago = Pedido.EstadoPago.APROBADO
                        order.estado_pedido = Pedido.EstadoPedido.PAGADO
                    else:
                        order.estado_pago = Pedido.EstadoPago.PENDIENTE

                    for item in items:
                        product = locked_products[item["product"].id]
                        product.stock -= item["quantity"]
                        product.contador_ventas += item["quantity"]
                        product.save(update_fields=["stock", "contador_ventas", "updated_at"])
                else:
                    order.estado_pago = Pedido.EstadoPago.RECHAZADO
                    order.estado_pedido = Pedido.EstadoPedido.CANCELADO

                order.save(
                    update_fields=[
                        "estado_pago",
                        "estado_pedido",
                        "referencia_pago",
                        "mensaje_pago",
                        "updated_at",
                    ]
                )

            _save_cart(request, {})
            if payment_result.approved:
                messages.success(request, "Pedido creado correctamente.")
            else:
                messages.warning(request, "Pedido registrado, pero el pago fue rechazado.")
            return redirect("checkout_success", codigo=order.codigo)
    else:
        form = CheckoutForm(
            initial={
                "tipo_entrega": Pedido.TipoEntrega.RETIRO,
                "metodo_pago": Pedido.MetodoPago.MOCK_CARD,
            }
        )

    return render(
        request,
        "MainApp/checkout/checkout.html",
        {
            "items": items,
            "total": total,
            "form": form,
        },
    )


@login_required
def checkout_success(request, codigo):
    order = get_object_or_404(
        Pedido.objects.prefetch_related("detalles__producto"),
        codigo=codigo,
        usuario=request.user,
    )
    return render(request, "MainApp/checkout/success.html", {"order": order})


def order_tracking(request, token):
    order = get_object_or_404(Pedido.objects.prefetch_related("detalles__producto"), tracking_token=token)
    return render(request, "MainApp/tracking/detail.html", {"order": order})

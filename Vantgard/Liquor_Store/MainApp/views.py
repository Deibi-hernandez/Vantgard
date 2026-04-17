from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CustomerRegistrationForm
from .models import Blog, Producto


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
    return render(request, "MainApp/account.html")

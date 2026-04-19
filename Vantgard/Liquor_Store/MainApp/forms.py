from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser, Pedido, Producto


class CustomerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "username": "usuario",
            "first_name": "nombre",
            "last_name": "apellido",
            "email": "correo@ejemplo.cl",
            "password1": "contrasena segura",
            "password2": "repite tu contrasena",
        }
        for field_name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "class": "form-control",
                    "placeholder": placeholders.get(field_name, ""),
                }
            )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.role = CustomUser.Role.CLIENTE
        user.is_staff = False

        if commit:
            user.save()

        return user

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta registrada con este correo.")
        return email


class CartAddForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1)


class CartUpdateForm(forms.Form):
    quantity = forms.IntegerField(min_value=1)


class CheckoutForm(forms.Form):
    tipo_entrega = forms.ChoiceField(choices=Pedido.TipoEntrega.choices)
    metodo_pago = forms.ChoiceField(choices=Pedido.MetodoPago.choices)
    direccion = forms.CharField(max_length=255, required=False)
    comuna = forms.CharField(max_length=80, required=False)
    sector = forms.CharField(max_length=80, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

    def clean(self):
        cleaned_data = super().clean()
        tipo_entrega = cleaned_data.get("tipo_entrega")

        if tipo_entrega != Pedido.TipoEntrega.RETIRO:
            missing_fields = [
                field_name
                for field_name in ("direccion", "comuna", "sector")
                if not cleaned_data.get(field_name)
            ]
            for field in missing_fields:
                self.add_error(field, "Este campo es obligatorio para envios.")

        return cleaned_data


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        is_offer = cleaned_data.get("is_offer")
        discount_percent = cleaned_data.get("discount_percent", 0) or 0
        stock = cleaned_data.get("stock")
        precio = cleaned_data.get("precio")

        if precio is not None and precio <= 0:
            self.add_error("precio", "El precio debe ser mayor a 0.")

        if stock is not None and stock < 0:
            self.add_error("stock", "El stock no puede ser negativo.")

        if is_offer and discount_percent <= 0:
            self.add_error("discount_percent", "Debes indicar un descuento valido para una oferta.")

        if not is_offer and discount_percent:
            self.add_error("discount_percent", "El descuento solo aplica a productos en oferta.")

        return cleaned_data

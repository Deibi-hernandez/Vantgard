from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser, Pedido


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

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


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

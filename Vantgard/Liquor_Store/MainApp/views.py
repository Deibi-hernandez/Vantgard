from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import CustomerRegistrationForm


def home(request):
    return render(request, 'MainApp/home.html')


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

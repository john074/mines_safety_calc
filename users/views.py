from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import CustomAuthenticationForm

# Create your views here.
def login_view(request):
    if request.method == "POST":
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("users:account")
    else:
        form = CustomAuthenticationForm()
    return render(request, "users/login.html", { "form": form })


def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("users:login")


@login_required(login_url="/users/login/")
def account_view(requset):
    return render(requset, "users/account.html")

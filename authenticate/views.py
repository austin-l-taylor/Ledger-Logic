from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .forms import SignUpForm


def login_user(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "You have successfully logged in.")
            return redirect("home")
        else:
            messages.success(request, "Invalid username or password.")
            return redirect("login")
    else:
        return render(request, "authenticate/login.html", {})


def logout_user(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect("login")


def register_user(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password1")
            # input admin use authentication here
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, "You have successfully registered.")
            return redirect("home")
    else:
        form = SignUpForm()
    context = {"form": form}
    return render(request, "authenticate/register.html", context)


def forgot_password(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

    return render(request, "authenticate/forgot_password.html", {})


def home(request):
    return render(request, "main_page/home.html", {})

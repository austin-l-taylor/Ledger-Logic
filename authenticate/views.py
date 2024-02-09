from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from authenticate.models import CustomUser
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
            user = form.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, "You have successfully registered.")
            return redirect("home")
    else:
        form = SignUpForm()

    context = {"form": form}
    return render(request, "authenticate/register.html", context)


def forgot_password(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        user = CustomUser.objects.filter(username=username, email=email)

        if user.exists():
            return redirect("question")
        else:
            # Add an error message to the messages framework
            messages.error(request, "No user found with this username and email")
            return redirect("forgot_password")
    return render(request, "authenticate/forgot_password.html", {})


def question(request):
    return render(request, "authenticate/question.html", {})


def home(request):
    return render(request, "main_page/home.html", {})

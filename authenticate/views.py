from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from authenticate.models import CustomUser
from .forms import SignUpForm, SecurityQuestionForm, ForgotPasswordForm
from .models import CustomUser


def login_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_suspended:
                messages.error(request, "Your account has been suspended.")
                return redirect("login")
            else:
                login(request, user)
                user.failed_login_attempts = 0
                user.save()
                messages.success(request, "You have successfully logged in.")
                return redirect("home")
        else:
            try:
                user = CustomUser.objects.get(username=username)
                if user.failed_login_attempts >= 4:
                    user.is_suspended = True
                    user.failed_login_attempts = 0
                    user.save()
                    messages.error(
                        request,
                        "You've attempted too many times. Your account has been suspended. An admin will need to unlock it.",
                    )
                else:
                    user.failed_login_attempts += 1
                    user.save()
                    messages.error(request, "Invalid username or password.")
            except CustomUser.DoesNotExist:
                messages.error(request, "Invalid username or password.")

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
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            email = form.cleaned_data.get("email")
            user = CustomUser.objects.filter(username=username, email=email)
            if user.exists():
                request.session["username"] = username
                return redirect("question")
            else:
                messages.error(request, "No user found with this username and email")
    else:
        form = ForgotPasswordForm()
    return render(request, "authenticate/forgot_password.html", {"form": form})


def question(request):
    username = request.session.get("username")
    if request.method == "POST":
        form = SecurityQuestionForm(request.POST)
        if form.is_valid():
            user_answer1 = request.POST.get("answer1")
            user_answer2 = request.POST.get("answer2")
            user = CustomUser.objects.get(username=username)
            if user.answer1 == user_answer1 and user.answer2 == user_answer2:
                return redirect("reset_password")
            else:
                messages.error(request, "Your answers do not match please try again.")
    else:
        form = SecurityQuestionForm()
    return render(request, "authenticate/question.html", {"form": form})


def reset_password(request):
    if request.method == "POST":
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        if password1 == password2:
            # Get the username from the session and get the corresponding user
            username = request.session.get("username")
            if username is None:
                messages.error(request, "No user found.")
                return redirect("question")
            user = CustomUser.objects.get(username=username)
            user.set_password(password1)
            user.save()
            messages.success(request, "Your password has been reset.")
            return redirect("login")
        else:
            messages.error(request, "Your passwords do not match.")
    return render(request, "authenticate/reset_password.html", {})


def home(request):
    return render(request, "main_page/home.html", {})

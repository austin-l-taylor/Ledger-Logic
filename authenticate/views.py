from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .forms import SignUpForm
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
                    messages.error(request, "You've attempted too many times. Your account has been suspended. An admin will need to unlock it.")
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
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "You have successfully registered.")
            return redirect("home")
    else:
        form = SignUpForm()
    
    context = {"form": form}
    return render(request, "authenticate/register.html", context)


def home(request):
    return render(request, "main_page/home.html", {})

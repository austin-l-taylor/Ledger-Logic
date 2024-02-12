from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from authenticate.models import CustomUser
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.admin.views.decorators import user_passes_test
from .forms import SignUpForm, SecurityQuestionForm, ForgotPasswordForm, EmailForm
from .models import CustomUser
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.template.loader import get_template
from django.template import Context
from django.utils.http import  urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMultiAlternatives
from .tokens import account_activation_token


def login_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        try:
            user = CustomUser.objects.get(username=username)
            if user.suspension_start_date and user.suspension_end_date:
                if user.suspension_start_date <= timezone.now().date() <= user.suspension_end_date:
                    user.is_suspended = True
                elif timezone.now().date() > user.suspension_end_date: 
                    user.is_suspended = False
                    user.suspension_start_date = None 
                    user.suspension_end_date = None
                user.save()

            if not user.is_suspended:
                user = authenticate(request, username=username, password=password)
                if user:
                    login(request, user)
                    user.failed_login_attempts = 0
                    user.save()
                    messages.success(request, "You have successfully logged in!")
                    return redirect("home")
                else:
                    user.failed_login_attempts += 1
                    if(user.failed_login_attempts >= 5):
                        user.is_suspended = True
                        user.failed_login_attempts = 0
                        user.save()
                        messages.error(request, "You've attempted too many times. Your account has been suspended.")
                    else:
                        user.save()
                        messages.error(request, "Invalid username or password.")
            else:
                messages.error(request, "Your account has been suspended. Reach out to an admin to unlock it.")
        except CustomUser.DoesNotExist:
            messages.error(request, "Invalid username or password.")

        return redirect("login")
    else:
        return render(request, "authenticate/login.html", {})


def logout_user(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect("login")

def activate(request, uidb64, token):
    User= get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        mail_subject = "You are able to login now!"
        mail_content = "Your account is now activated. You can login now. Thanks!"
        from_email = "ledgerlogic.ksu@gmail.com"
        to_email = user.email
        message = EmailMultiAlternatives(mail_subject, mail_content, from_email, [to_email])
        message.send()
        messages.success(request, "User account is now active.")
        return redirect("authenticate/home.html")
    else:
        messages.error(request, "Activation link is invalid!")
    return redirect("authenticate/home.html")

def activationEmail(request, user, username):
    mail_subject = "A new user has registered to your site."
    message = render_to_string("activationAccount.html", {
        "user": username,
        'useremail': user.email,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        "protcol":'https' if request.is_secure() else 'http'
    })
    email = EmailMultiAlternatives(mail_subject, message, to=["myin1@students.kennesaw.edu"])
    email.send()


def register_user(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active=False
            user.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, "You have successfully registered.")
            activationEmail(request, user, form.cleaned_data.get('username'))
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

def is_staff_user(user):
    return user.is_staff

@user_passes_test(is_staff_user)
def send_email_view(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id)
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False
            )
            messages.success(request, "Email sent!")
            return redirect('admin:index')
    else:
        form = EmailForm()
    return render(request, 'admin_custom/send_email.html', {'form': form, 'user': user})
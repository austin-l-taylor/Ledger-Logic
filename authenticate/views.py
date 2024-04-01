from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from authenticate.models import CustomUser
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.admin.views.decorators import user_passes_test
from .forms import (
    SignUpForm,
    SecurityQuestionForm,
    ForgotPasswordForm,
    EmailForm,
    ChartOfAccountForm,
)
from .models import CustomUser, ChartOfAccounts, CoAEventLog, JournalEntry, GeneralLedger
from django.conf import settings
from django.utils import timezone
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string , get_template
from django.template import Context
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMultiAlternatives
from .tokens import account_activation_token
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.db.models import Sum
from django.contrib.auth.hashers import check_password
from decimal import Decimal




def ledger(request, account_id):
    account = get_object_or_404(ChartOfAccounts, id=account_id)
    
    # Filter journal entries by account and order by date
    journal_entries = JournalEntry.objects.filter(account=account).order_by('date')
    
    initial_balance = account.initial_balance
    current_balance = initial_balance

    for entry in journal_entries:
        # Calculate the balance for each entry
        entry.balance = current_balance + entry.debit - entry.credit
        current_balance = entry.balance

    return render(request, "main_page/ledger.html", {"journal_entries": journal_entries, "account": account})


def serialize_account(instance):
    # Fetch related user instance
    user = instance.user_id

    # Convert DateTimeField to ISO format
    date_time_account_added = (
        instance.date_time_account_added.isoformat()
        if instance.date_time_account_added
        else None
    )

    # Construct a dictionary of fields to serialize
    serialized_data = {
        "account_name": instance.account_name,
        "account_number": instance.account_number,
        "account_description": instance.account_description,
        "is_active": instance.is_active,
        "normal_side": instance.normal_side,
        "account_category": instance.account_category,
        "account_subcategory": instance.account_subcategory,
        "initial_balance": (
            float(instance.initial_balance)
            if instance.initial_balance is not None
            else None
        ),
        "debit": float(instance.debit) if instance.debit is not None else None,
        "credit": float(instance.credit) if instance.credit is not None else None,
        "balance": float(instance.balance) if instance.balance is not None else None,
        "date_time_account_added": date_time_account_added,
        "user_id": {
            "id": user.id,
            "username": user.username,
        },
        "order": instance.order,
        "statement": instance.statement,
        "comment": instance.comment,
    }

    # Serialize data using Django's JSON encoder
    serialized_json = json.dumps(serialized_data, cls=DjangoJSONEncoder)
    return serialized_json


from django.db.models import Q


def login_user(request):
    """
    Handles the login process for a user.

    This function authenticates the user based on the username and password provided in the POST request.
    If the user is found and not suspended, it logs the user in and resets their failed login attempts.
    If the user is not found or the password is incorrect, it increments their failed login attempts.
    If the user has 5 or more failed login attempts, it suspends the user's account.
    If the user's account is suspended, it sends an error message.
    If the user's suspension has ended, it unsuspends the user's account.

    Parameters:
    request (HttpRequest): The HTTP request object.

    Returns:
    HttpResponse: The HTTP response. Redirects to the home page on successful login, or back to the login page on failure.
    """
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.suspension_start_date and user.suspension_end_date:
                if (
                    user.suspension_start_date
                    <= timezone.now().date()
                    <= user.suspension_end_date
                ):
                    user.is_suspended = True
                elif timezone.now().date() > user.suspension_end_date:
                    user.is_suspended = False
                    user.suspension_start_date = None
                    user.suspension_end_date = None
                user.save()

            if not user.is_suspended:
                login(request, user)
                user.failed_login_attempts = 0
                user.save()
                messages.success(request, "You have successfully logged in!")
                return redirect("home")
            else:
                messages.error(
                    request,
                    "Your account has been suspended. Reach out to an admin to unlock it.",
                )
        else:
            try:
                user = CustomUser.objects.get(username=username)
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.is_suspended = True
                    user.failed_login_attempts = 0
                    user.save()
                    messages.error(
                        request,
                        "You've attempted too many times. Your account has been suspended.",
                    )
                else:
                    user.save()
                    messages.error(request, "Invalid username or password.")
            except CustomUser.DoesNotExist:
                messages.error(request, "Invalid username or password.")

        return redirect("login")
    else:
        return render(request, "authenticate/login.html", {})


def logout_user(request):
    """
    Logs out the current user and redirects to the login page.

    Parameters:
    request (HttpRequest): The HTTP request object.

    Returns:
    HttpResponse: The HTTP response. Redirects to the login page.
    """
    # Log the user out
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect("login")


def activate(request, uidb64, token):
    User = get_user_model()
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
        message = EmailMultiAlternatives(
            mail_subject, mail_content, from_email, [to_email]
        )
        message.send()
        messages.success(request, "User account is now active.")
        return redirect("home")
    else:
        messages.error(request, "Activation link is invalid!")
    return redirect("authenticate/login.html")


def activationEmail(request, user, username):
    mail_subject = "A new user has registered to your site."
    message = render_to_string(
        "activationAccount.html",
        {
            "user": username,
            "useremail": user.email,
            "domain": get_current_site(request).domain,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": account_activation_token.make_token(user),
            "protcol": "https" if request.is_secure() else "http",
        },
    )
    email = EmailMultiAlternatives(
        mail_subject, message, to=["jochoa2@students.kennesaw.edu"]
    )
    email.send()


def register_user(request):
    """
    Handles user registration. If the request method is POST and the form is valid, it creates a new user and logs them in.

    Parameters:
    request (HttpRequest): The HTTP request object.

    Returns:
    HttpResponse: The HTTP response. Renders the registration form on GET requests or invalid POST requests. Redirects to the home page on successful registration.
    """
    # Check if the request method is POST
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(
                request,
                "You have successfully registered. Please wait for admin to confirm your account.",
            )
            activationEmail(request, user, form.cleaned_data.get("username"))
            return redirect("login")
    # If the request method is not POST
    else:
        form = SignUpForm()

    context = {"form": form}
    return render(request, "authenticate/register.html", context)


def forgot_password(request):
    """
    Handles the forgot password process. If the request method is POST and the form is valid, it checks if a user with the provided username and email exists.

    Parameters:
    request (HttpRequest): The HTTP request object.

    Returns:
    HttpResponse: The HTTP response. Renders the forgot password form on GET requests or invalid POST requests. Redirects to the security question page if a user with the provided username and email exists.
    """
    # Check if the request method is POST
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        # Check if the form is valid
        if form.is_valid():
            username = form.cleaned_data.get("username")
            email = form.cleaned_data.get("email")
            user = CustomUser.objects.filter(username=username, email=email)
            # Check if a user with the provided username and email exists
            if user.exists():
                request.session["username"] = username
                return redirect("question")
            else:
                messages.error(request, "No user found with this username and email")
    else:
        # If the request method is not POST
        form = ForgotPasswordForm()
    return render(request, "authenticate/forgot_password.html", {"form": form})


def question(request):
    """
    Handles the security question verification process. If the request method is POST and the form is valid, it checks if the provided answers match the user's answers.

    Parameters:
    request (HttpRequest): The HTTP request object.

    Returns:
    HttpResponse: The HTTP response. Renders the security question form on GET requests or invalid POST requests. Redirects to the reset password page if the provided answers match the user's answers.
    """
    username = request.session.get("username")
    # Check if the request method is POST
    if request.method == "POST":
        form = SecurityQuestionForm(request.POST)
        # Check if the form is valid
        if form.is_valid():
            user_answer1 = request.POST.get("answer1")
            user_answer2 = request.POST.get("answer2")
            user = CustomUser.objects.get(username=username)
            # Check if the provided answers match the user's answers
            if user.answer1 == user_answer1 and user.answer2 == user_answer2:
                return redirect("reset_password")
            else:
                messages.error(request, "Your answers do not match please try again.")
    else:
        form = SecurityQuestionForm()
    return render(request, "authenticate/question.html", {"form": form})


def reset_password(request):
    """
    Handles the password reset process. If the request method is POST, it checks if the provided passwords match and if a user with the username stored in the session exists.

    Parameters:
    request (HttpRequest): The HTTP request object.

    Returns:
    HttpResponse: The HTTP response. Renders the reset password form on GET requests. Redirects to the login page on successful password reset.
    """
    # Check if the request method is POST
    if request.method == "POST":
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        # Check if the provided passwords match
        if password1 == password2:
            # Get the username from the session and get the corresponding user
            username = request.session.get("username")
            # Check if a user with the username stored in the session exists
            if username is None:
                messages.error(request, "No user found.")
                return redirect("question")
            user = CustomUser.objects.get(username=username)
            password_histories = user.password
            if check_password(password1, password_histories):
                messages.error(request, "That password has already been used")
                return redirect("reset_password")
            user.set_password(password1)
            user.save()
            # Clear the session
            messages.success(request, "Your password has been reset.")
            return redirect("login")
        # If the provided passwords do not match
        else:
            messages.error(request, "Your passwords do not match.")
    return render(request, "authenticate/reset_password.html", {})


def home(request):
    """
    Renders the home page.

    Parameters:
    request (HttpRequest): The HTTP request object.

    Returns:
    HttpResponse: The HTTP response. Renders the home page.
    """
    return render(request, "main_page/home.html", {})


def help(request):
    """same as above but for the help page"""
    return render(request, "main_page/help.html", {})


def is_staff_user(user):
    """
    Checks if a user is a staff user.

    Parameters:
    user (User): The user to check.

    Returns:
    bool: True if the user is a staff user, False otherwise.
    """
    return user.is_staff


@user_passes_test(is_staff_user)
def send_email_view(request, user_id):
    """
    Handles the email sending process. If the request method is POST and the form is valid, it sends an email to the user with the provided user ID.

    Parameters:
    request (HttpRequest): The HTTP request object.
    user_id (int): The ID of the user to send the email to.

    Returns:
    HttpResponse: The HTTP response. Renders the email form on GET requests or invalid POST requests. Redirects to the admin index page on successful email sending.
    """
    user = get_object_or_404(CustomUser, pk=user_id)
    # Check if the request method is POST
    if request.method == "POST":
        form = EmailForm(request.POST)
        # Check if the form is valid
        if form.is_valid():
            # Send an email to the user
            subject = form.cleaned_data["subject"]
            message = form.cleaned_data["message"]
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            # Save the email notification
            messages.success(request, "Email sent!")
            return redirect("admin:index")
    # If the request method is not POST
    else:
        form = EmailForm()
    return render(request, "admin_custom/send_email.html", {"form": form, "user": user})


@login_required
def chart_of_accounts(request):
    """
    Renders the chart of accounts page but also checks if the user is an admin.
    """
    query = request.GET.get("q")
    is_admin = request.user.is_superuser  # Determine if the user is an admin
    selected_account = request.GET.get("selected_account")
    if selected_account:
        return redirect("ledger", account_id=selected_account)

    if query:
        accounts = ChartOfAccounts.objects.filter(
            Q(account_name__icontains=query)
            | Q(account_number__icontains=query)
            | Q(account_description__icontains=query)
            | Q(account_category__icontains=query)
            | Q(account_subcategory__icontains=query)
        ).order_by("order")
    else:
        accounts = ChartOfAccounts.objects.all().order_by(
            "order",
        )  # Fetch all accounts, ordered by 'order'

    # Pass the accounts and is_admin flag to the template
    context = {
        "accounts": accounts,
        "is_admin": is_admin,
    }
    return render(request, "main_page/chart_of_accounts.html", context)





@user_passes_test(lambda u: u.is_superuser)
def add_account(request):
    """
    Definition that handles adding a new account to the Chart of Accounts.

    The only thing that you won't see in the table is the user_id field.
    This is because the user_id field is automatically set to the current user when the account is added below.
    """
    if request.method == "POST":
        form = ChartOfAccountForm(request.POST)
        if form.is_valid():
            user_instance = get_object_or_404(CustomUser, id=request.user.id)
            form.instance.user_id = user_instance
            form.save()
            messages.success(request, "Account added!")
            return redirect("chart_of_accounts")
    else:
        form = ChartOfAccountForm()
    return render(request, "main_page/add_coa_account.html", {"form": form})


def edit_account(request, account_id):
    """
    Definition that handles editing an account in the Chart of Accounts.

    This one is also handling the JSON serialization of the before and after changes. Which can be viewed in the view_coa_logs.html page.
    """
    account = get_object_or_404(ChartOfAccounts, id=account_id)

    if request.method == "POST":
        form = ChartOfAccountForm(request.POST, instance=account)
        if form.is_valid():
            before_edit_snapshot = serialize_account(
                account
            )  # Serialize before making changes
            form.save()
            after_edit_snapshot = serialize_account(
                account
            )  # Serialize after saving changes

            # Log the change
            CoAEventLog.objects.create(
                user=request.user,
                action="modified",
                before_change=before_edit_snapshot,
                after_change=after_edit_snapshot,
                chart_of_account=account,
            )
            messages.success(request, "Account updated successfully!")
            return redirect("chart_of_accounts")
    else:
        form = ChartOfAccountForm(instance=account)
    return render(request, "main_page/edit_coa_account.html", {"form": form})


@user_passes_test(lambda u: u.is_superuser)
def deactivate_account(request, account_id):
    """
    Definition that handles deactivating an account in the Chart of Accounts.
    Accounts with a balance greater than 0 cannot be deactivated.
    """
    account = get_object_or_404(ChartOfAccounts, id=account_id)

    # Check if the account has a balance greater than 0
    balance = ChartOfAccounts.objects.filter(id=account_id).aggregate(Sum("balance"))[
        "balance__sum"
    ]
    if balance is not None and balance > 0:
        messages.error(
            request, "Accounts with a balance greater than 0 cannot be deactivated."
        )
        return redirect("chart_of_accounts")

    before_change = serialize("json", [account])

    account.is_active = False
    account.save()

    after_change = serialize("json", [account])

    CoAEventLog.objects.create(
        user=request.user,
        action="deactivated",
        before_change=before_change,
        after_change=after_change,
        timestamp=now(),
        chart_of_account=account,
    )

    return redirect("chart_of_accounts")


@user_passes_test(lambda u: u.is_superuser)
def activate_account(request, account_id):
    """
    Definition that handles activating an account in the Chart of Accounts.

    This one is also handling the JSON serialization of the before and after changes. Which can be viewed in the view_coa_logs.html page.
    """
    account = get_object_or_404(ChartOfAccounts, id=account_id)
    before_change = serialize("json", [account])

    account.is_active = True
    account.save()

    after_change = serialize("json", [account])

    CoAEventLog.objects.create(
        user=request.user,
        action="activated",
        before_change=before_change,
        after_change=after_change,
        timestamp=now(),
        chart_of_account=account,
    )

    return redirect("chart_of_accounts")


@user_passes_test(lambda u: u.is_superuser)
def view_coa_logs(request):
    """
    Definition that handles viewing the Chart of Accounts event logs.

    This one is also handling the JSON serialization of the before and after changes.
    However, the JSON data is currently not correctly in the view_coa_logs.html page.
    This one needs to be fixed if we have time!!!!!!!!!!!!!!!!

    """
    # Fetch all log changes
    logs = CoAEventLog.objects.all()

    # Serialize the before_change and after_change fields as JSON strings
    serialized_logs = []
    for log in logs:
        before_change = log.before_change
        after_change = log.after_change

        # Parse JSON strings into Python objects
        before_change_data = json.loads(before_change) if before_change else None
        after_change_data = json.loads(after_change) if after_change else None

        serialized_logs.append(
            {
                "user": log.user.username,
                "action": log.action,
                "timestamp": log.timestamp,
                "before_change": before_change_data,
                "after_change": after_change_data,
            }
        )

    return render(request, "main_page/view_coa_logs.html", {"logs": serialized_logs})


def format_change_data(data):
    """
    This function formats the change data to a string.
    This is where we might be able to fix the issue with the JSON data not showing correctly in the view_coa_logs.html page.
    """
    formatted_change = ""
    for change in data:
        fields = change.get("fields", {})
        for key, value in fields.items():
            formatted_change += f"{key}: {value} ;"
    return formatted_change


def journal_entry_page(request):
    if request.method == "POST":
        if "approve" in request.POST:
            entry_id = request.POST.get("entry_id")
            entry = JournalEntry.objects.get(id=entry_id)
            entry.status = "Approved"  # Adjust the status based on your model
            entry.save()

        elif "reject" in request.POST:
            entry_id = request.POST.get("entry_id")
            entry = JournalEntry.objects.get(id=entry_id)
            entry.status = "Rejected"  # Adjust the status based on your model
            entry.save()

        return redirect("journal_entry_page")

    else:
        journal_entries = JournalEntry.objects.all()
        is_admin = request.user.is_staff
        return render(
            request,
            "main_page/journal_entry_page.html",
            {"journal_entries": journal_entries, "is_admin": is_admin},
        )


def add_journal_entry(request):
    if request.method == "POST":
        # Extract data from form
        account1_name = request.POST.get("account1")
        debit1 = Decimal(request.POST.get("debit1", 0))
        credit1 = Decimal(request.POST.get("credit1", 0))
        date1 = request.POST.get("date1")
        comments1 = request.POST.get("comments1")
        attachment1 = request.FILES.get("attachment1")

        account2_name = request.POST.get("account2")
        debit2 = Decimal(request.POST.get("debit2", 0))
        credit2 = Decimal(request.POST.get("credit2", 0))
        date2 = request.POST.get("date2")
        comments2 = request.POST.get("comments2")
        attachment2 = request.FILES.get("attachment2")

        try:
            # Check if accounts exist in the Chart of Accounts
            account1 = ChartOfAccounts.objects.get(account_name=account1_name)
            account2 = ChartOfAccounts.objects.get(account_name=account2_name)

            # Update debit and credit for account1
            account1.debit += debit1
            account1.credit += credit1
            account1.save()

            # Update debit and credit for account2
            account2.debit += debit2
            account2.credit += credit2
            account2.save()

            # Create the Journal Entries
            JournalEntry.objects.create(
                account=account1,
                debit=debit1,
                credit=credit1,
                date=date1,
                comments=comments1,
                attachment=attachment1,
                status="Pending",
            )
            JournalEntry.objects.create(
                account=account2,
                debit=debit2,
                credit=credit2,
                date=date2,
                comments=comments2,
                attachment=attachment2,
                status="Pending",
            )

        except ChartOfAccounts.DoesNotExist:
            # Handle the case where the account does not exist
            messages.error(
                request, "One or more accounts do not exist in the Chart of Accounts."
            )
            return render(request, "main_page/add_journal_entry_page.html")

        return redirect("journal_entry_page")
    else:
        return render(request, "main_page/add_journal_entry_page.html")

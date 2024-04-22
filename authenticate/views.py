# Django imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.admin.views.decorators import user_passes_test
from django.conf import settings
from django.utils import timezone
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string, get_template
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers import serialize
from django.db.models import Sum, Q
from django.contrib.auth.hashers import check_password
from django.http import HttpResponseRedirect, FileResponse, HttpResponse



# Local imports
from .forms import (
    SignUpForm,
    SecurityQuestionForm,
    ForgotPasswordForm,
    EmailForm,
    ChartOfAccountForm,
    ContactForm,
    ContactFormAdmin,
    CommentForm,
)
from .models import (
    CustomUser,
    ChartOfAccounts,
    CoAEventLog,
    JournalEntry,
    JournalEntryGroup,
)
from .tokens import account_activation_token

# Other imports
import json
from decimal import Decimal
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from xhtml2pdf import pisa


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
        "authenticate/activationAccount.html",
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
    if is_admin:
        formSelection = ContactFormAdmin
    else:
        formSelection = ContactForm

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

    if request.method == "POST":
        if request.user.is_superuser:
            # Email to User
            form = ContactFormAdmin(request.POST)
        else:
            # Email to Admin
            form = ContactForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data.get("email")
            To = form.cleaned_data.get("To")
            subject = form.cleaned_data.get("subject")
            message = form.cleaned_data.get("message")
            full_message = f"""
  		        {email} has submitted an email to the Admins.
		        Subject: {subject}
		        Message: {message}


                """
            send_mail(
                subject=subject,
                message=full_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[To],
            )
            messages.success(request, "Email sent!")
            return HttpResponseRedirect(request.path_info)
    # Pass the accounts and is_admin flag to the template
    context = {
        "accounts": accounts,
        "is_admin": is_admin,
        "form": formSelection,
    }
    return render(
        request, "main_page/chart_of_accounts/chart_of_accounts.html", context
    )


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
    return render(
        request, "main_page/chart_of_accounts/add_coa_account.html", {"form": form}
    )


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
    return render(
        request, "main_page/chart_of_accounts/edit_coa_account.html", {"form": form}
    )


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

    return render(
        request,
        "main_page/chart_of_accounts/view_coa_logs.html",
        {"logs": serialized_logs},
    )


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
            group_id = request.POST.get("group_id")
            print(group_id)
            entries = JournalEntry.objects.filter(group_id=group_id)
            add_comment(request, group_id)
            for entry in entries:
                entry.approve()
                # Perform the calculation here after the entry has been approved
                account = entry.account
                account.save()

        elif "reject" in request.POST:
            group_id = request.POST.get("group_id")
            print(group_id)
            entries = JournalEntry.objects.filter(group_id=group_id)
            for entry in entries:
                add_comment(request, group_id)
                entry.status = "Rejected"
                entry.save()

        return redirect("journal_entry_page")

    else:
        journal_entries = JournalEntry.objects.all()
        is_admin = request.user.is_staff
        return render(
            request,
            "main_page/journal_entry/journal_entry_page.html",
            {"journal_entries": journal_entries, "is_admin": is_admin},
        )


def add_journal_entry(request):
    if request.method == "POST":
        # Extract data from form
        account1_name = request.POST.get("account1")
        debit = Decimal(request.POST.get("debit1", 0))
        date1 = request.POST.get("date1")
        comments1 = request.POST.get("comments1")
        attachment1 = request.FILES.get("attachment1")

        account2_name = request.POST.get("account2")
        credit = Decimal(request.POST.get("credit2", 0))
        date2 = request.POST.get("date2")
        comments2 = request.POST.get("comments2")
        attachment2 = request.FILES.get("attachment2")

        # Check if debit and credit values match
        if debit != credit:
            messages.error(request, "The total debit and credit values must match.")
            return render(
                request, "main_page/journal_entry/add_journal_entry_page.html"
            )

        try:
            # Check if accounts exist in the Chart of Accounts
            account1 = ChartOfAccounts.objects.get(account_name=account1_name)
            account2 = ChartOfAccounts.objects.get(account_name=account2_name)

            # Check if account1 is a normal side left account
            if account1.normal_side != "Left":
                messages.error(request, "Account 1 must be a normal side left account.")
                return render(
                    request, "main_page/journal_entry/add_journal_entry_page.html"
                )
            elif account2.normal_side != "Right":
                messages.error(
                    request, "Account 2 must be a normal side right account."
                )
                return render(
                    request, "main_page/journal_entry/add_journal_entry_page.html"
                )

            # Create a JournalEntryGroup
            group = JournalEntryGroup.objects.create()

            # Create the Journal Entries
            JournalEntry.objects.create(
                account=account1,
                debit=debit,
                date=date1,
                comments=comments1,
                attachment=attachment1,
                status="Pending",
                group=group,
            )
            JournalEntry.objects.create(
                account=account2,
                credit=credit,
                date=date2,
                comments=comments2,
                attachment=attachment2,
                status="Pending",
                group=group,
            )

        except ChartOfAccounts.DoesNotExist:
            # Handle the case where the account does not exist
            messages.error(
                request, "One or more accounts do not exist in the Chart of Accounts."
            )
            return render(
                request, "main_page/journal_entry/add_journal_entry_page.html"
            )
        journalEntryEmail(
            request,
            account1,
            debit,
            comments1,
            account2,
            credit,
            comments2,
        )
        return redirect("journal_entry_page")
    else:
        return render(request, "main_page/journal_entry/add_journal_entry_page.html")


def add_comment(request, group_id):
    try:
        entry = JournalEntry.objects.get(id=group_id)
    except JournalEntry.DoesNotExist:
        # Handle the error. For example, you could return early:
        return
    # Rest of the function...


def journalEntryEmail(
    request,
    account1Name,
    acct1debit,
    account1,
    account2Name,
    acct2credit,
    account2,
):
    mail_subject = "A new journal entry has been posted to your site."
    message = render_to_string(
        "main_page/journal_entry/journalEntryEmail.html",
        {
            "account1Name": account1Name,
            "account1Debit": acct1debit,
            "account1": account1,
            "account2Name": account2Name,
            "account2Credit": acct2credit,
            "account2": account2,
            "domain": get_current_site(request).domain,
        },
    )
    email = EmailMultiAlternatives(
        mail_subject, message, to=["myin1@students.kennesaw.edu"]
    )
    email.send()


def entry_details(request, entry_id):
    """
    View function to display details of a specific journal entry.
    """
    journal_entry = get_object_or_404(JournalEntry, id=entry_id)
    is_admin = request.user.is_staff
    return render(
        request,
        "main_page/ledger/entry_details.html",
        {"journal_entry": journal_entry, "is_admin": is_admin},
    )


def ledger(request, account_id):
    account = get_object_or_404(ChartOfAccounts, id=account_id)

    # Filter journal entries by account and order by date
    journal_entries = JournalEntry.objects.filter(account=account).order_by("date")

    initial_balance = account.initial_balance
    current_balance = initial_balance

    for entry in journal_entries:
        # Calculate the balance for each entry
        entry.balance = current_balance + entry.debit - entry.credit
        current_balance = entry.balance

    return render(
        request,
        "main_page/ledger/ledger.html",
        {"journal_entries": journal_entries, "account": account},
    )


def email(request, email, subject, message):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            subject = form.cleaned_data.get("subject")
            message = form.cleaned_data.get("message")

            full_message = f"""
                Received message below from {email}, {subject}
                ________________________


                {message}
                """
            send_mail(
                subject="Received contact form submission",
                message=full_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["myin1@students.kennesaw.edu"],
            )
    return render(request, "main_page/contact.html", {"form": form})


def trial_balance(request):
    """
    Definition that handles the trial balance page.
    """
    formSelection = ContactForm
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date and end_date:
        journal_entries = JournalEntry.objects.filter(
            Q(date__gte=start_date) & Q(date__lte=end_date)
        )
    elif start_date:
        journal_entries = JournalEntry.objects.filter(date__gte=start_date)
    elif end_date:
        journal_entries = JournalEntry.objects.filter(date__lte=end_date)
    else:
        journal_entries = JournalEntry.objects.all()

    # Group by account and aggregate debit and credit values
    accounts = journal_entries.values("account__account_name").annotate(
        total_debit=Sum("debit"), total_credit=Sum("credit")
    )

    # Calculate total debit and credit
    total_debit = sum(account["total_debit"] for account in accounts)
    total_credit = sum(account["total_credit"] for account in accounts)

    return render(
        request,
        "main_page/forms/trial_balance.html",
        {
            "accounts": accounts,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "form": formSelection,
        },
    )


def income_statement(request):
    """
    View for the Income Statement page.
    """
    formSelection = ContactForm
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date and end_date:
        journal_entries = JournalEntry.objects.filter(
            date__range=[start_date, end_date]
        )
    elif start_date:
        journal_entries = JournalEntry.objects.filter(date__gte=start_date)
    elif end_date:
        journal_entries = JournalEntry.objects.filter(date__lte=end_date)
    else:
        journal_entries = JournalEntry.objects.all()

    # Group by account and calculate net income
    accounts = journal_entries.values("account__account_name").annotate(
        total_debit=Sum("debit"), total_credit=Sum("credit")
    )

    # Define revenue and expense account names
    revenue_account_names = ["Unearned Revenue"]
    expense_account_names = ["Accrued Expense", "Prepaid Expenses"]

    # Filter accounts based on revenue and expense account names
    revenue_accounts = [
        account
        for account in accounts
        if account["account__account_name"] in revenue_account_names
    ]
    expense_accounts = [
        account
        for account in accounts
        if account["account__account_name"] in expense_account_names
    ]

    # Calculate total revenue
    total_revenue = sum(
        account["total_credit"] - account["total_debit"] for account in revenue_accounts
    )

    # Calculate total expenses
    total_expenses = sum(
        account["total_debit"] - account["total_credit"] for account in expense_accounts
    )

    # Calculate net income
    net_income = total_revenue - total_expenses

    return render(
        request,
        "main_page/forms/income_statement.html",
        {
            "revenue_accounts": revenue_accounts,
            "expense_accounts": expense_accounts,
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "net_income": net_income,
            "start_date": start_date,
            "end_date": end_date,
            "form": formSelection,
        },
    )


def balance_sheet(request):
    """
    View for the balance sheet page.
    """
    formSelection = ContactForm
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date and end_date:
        journal_entries = JournalEntry.objects.filter(
            date__range=[start_date, end_date]
        )
    elif start_date:
        journal_entries = JournalEntry.objects.filter(date__gte=start_date)
    elif end_date:
        journal_entries = JournalEntry.objects.filter(date__lte=end_date)
    else:
        journal_entries = JournalEntry.objects.all()

    # Define categories
    assets_categories = ["Assets"]
    liabilities_categories = ["Liabilities"]
    equity_categories = ["Stockholders' Equity"]

    # Filter accounts based on categories
    asset_accounts = (
        ChartOfAccounts.objects.filter(account_category__in=assets_categories)
        .values("account_name")
        .annotate(total_debit=Sum("debit"), total_credit=Sum("credit"))
    )

    liability_accounts = (
        ChartOfAccounts.objects.filter(account_category__in=liabilities_categories)
        .values("account_name")
        .annotate(total_debit=Sum("debit"), total_credit=Sum("credit"))
    )

    equity_accounts = (
        ChartOfAccounts.objects.filter(account_category__in=equity_categories)
        .values("account_name")
        .annotate(total_debit=Sum("debit"), total_credit=Sum("credit"))
    )

    # Calculate totals
    total_assets = sum(
        account["total_debit"] - account["total_credit"] for account in asset_accounts
    )
    total_liabilities = sum(
        account["total_credit"] - account["total_debit"]
        for account in liability_accounts
    )
    total_equity = sum(
        account["total_credit"] - account["total_debit"] for account in equity_accounts
    )

    # Total Liabilities and Stockholders' Equity
    total_liabilities_and_equity = total_liabilities + total_equity
    if request.method == "POST":
            form = ContactForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data.get("email")
                subject = form.cleaned_data.get("subject")
                from_email=settings.DEFAULT_FROM_EMAIL,
                message = request.POST.get('document.Body')

                full_message = f"""
                    Received message below from {email}, {subject}
                    ________________________
                    {message}
                    """
                msg = send_mail(subject, full_message, email, ["myin1@students.kennesaw.edu"])
                msg.attach_alternative(message, 'application/pdf')
                msg.send()
                messages.success(request, "Email sent!")
                return HttpResponseRedirect(request.path_info)
    return render(
        request,
        "main_page/forms/balance_sheet.html",
        {
            "asset_accounts": asset_accounts,
            "liability_accounts": liability_accounts,
            "equity_accounts": equity_accounts,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "total_equity": total_equity,
            "total_liabilities_and_equity": total_liabilities_and_equity,
            "start_date": start_date,
            "end_date": end_date,
            "form": formSelection,
        },
    )


def export_to_pdf(request):
    print("export_to_pdf view was called")  # This will print to the console
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    # Load the template
    template = get_template("main_page/pdf_template.html")

    # Define the context for the template
    context = {
        "start_date": start_date,
        "end_date": end_date,
    }

    # Render the template with the context
    html = template.render(context)

    # Create a BytesIO object and generate the PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)

    # If there was an error, return a HTTP response
    if not pdf.err:
        return FileResponse(result, as_attachment=True, filename="report.pdf")
    else:
        return HttpResponse("Error generating PDF", status=500)


def retained_earnings(request):
    """
    Definition that handles the retained earnings page.
    """
    formSelection = ContactForm
    accounts = ChartOfAccounts.objects.all()
    return render(
        request, "main_page/forms/retained_earnings.html", {"accounts": accounts,"form": formSelection,}
    )


def calculate_ratios():
    """
    Calculate various financial ratios based on Chart of Accounts data.
    """

    # Color variables for the ratios
    GREEN = "#28a745"
    YELLOW = "#ffc107"
    RED = "#dc3545"

    # Retrieve all accounts
    accounts = ChartOfAccounts.objects.all()

    # Initialize variables for ratio calculations
    current_assets = 0
    current_liabilities = 0
    cash = 0
    operating_cash_flow = 0
    total_liabilities = 0
    total_assets = 0
    shareholder_equity = 0
    operating_income = 0
    interest_expenses = 0
    total_debt_service = 0
    net_sales = 0
    cost_of_goods_sold = 0
    gross_profit = 0
    net_income = 0
    inventory = 0
    net_credit_sales = 0
    average_accounts_receivable = 0

    # Assign values based on account name or category
    for account in accounts:
        if account.account_name == "Cash":
            cash = round(account.balance, 2)
        elif account.account_name == "Operating Cash":
            operating_cash_flow = round(account.balance, 2)
        elif account.account_name == "Total Debt Service":
            total_debt_service = round(account.balance, 2)
        elif account.account_name == "Operating Income":
            operating_income = round(account.balance, 2)
        elif account.account_name == "Interest Expense":
            interest_expenses = round(account.balance, 2)
        elif account.account_name == "Net Sales":
            net_sales = round(account.balance, 2)
        elif account.account_name == "Cost of Goods Sold":
            cost_of_goods_sold = round(account.balance, 2)
        elif account.account_name == "Gross Profit":
            gross_profit = round(account.balance, 2)
        elif account.account_name == "Net Income":
            net_income = round(account.balance, 2)
        elif account.account_name == "Inventory":
            inventory = round(account.balance, 2)
        elif account.account_category == "Assets":
            current_assets += round(account.balance, 2)
            total_assets += round(account.balance, 2)
        elif account.account_category == "Liabilities":
            current_liabilities += round(account.balance, 2)
            total_liabilities += round(account.balance, 2)
        elif account.account_category == "Equity":
            shareholder_equity += round(account.balance, 2)

    # Calculate ratios and round to two decimal places
    ratios = {}

    # Liquidity Ratios
    if current_liabilities != 0:
        current_ratio = round(current_assets / current_liabilities, 2)
        acid_test_ratio = round((current_assets - inventory) / current_liabilities, 2)
        cash_ratio = round(cash / current_liabilities, 2)
        operating_cash_flow_ratio = round(operating_cash_flow / current_liabilities, 2)

        ratios["current_ratio"] = {
            "value": current_ratio,
            "color": (
                GREEN if current_ratio >= 1.5 else YELLOW if current_ratio >= 1 else RED
            ),
        }
        ratios["acid_test_ratio"] = {
            "value": acid_test_ratio,
            "color": (
                GREEN
                if acid_test_ratio >= 1
                else YELLOW if acid_test_ratio >= 0.5 else RED
            ),
        }
        ratios["cash_ratio"] = {
            "value": cash_ratio,
            "color": (
                GREEN if cash_ratio >= 0.5 else YELLOW if cash_ratio >= 0.2 else RED
            ),
        }
        ratios["operating_cash_flow_ratio"] = {
            "value": operating_cash_flow_ratio,
            "color": (
                GREEN
                if operating_cash_flow_ratio >= 1
                else YELLOW if operating_cash_flow_ratio >= 0.5 else RED
            ),
        }

    # Leverage Financial Ratios
    if total_assets != 0 and total_liabilities != 0:
        debt_ratio = round(total_liabilities / total_assets, 2)
        debt_to_equity_ratio = round(total_liabilities / shareholder_equity, 2)
        interest_coverage_ratio = (
            round(operating_income / interest_expenses, 2) if interest_expenses else 0
        )
        debt_service_coverage_ratio = (
            round(operating_income / total_debt_service, 2) if total_debt_service else 0
        )

        ratios["debt_ratio"] = {
            "value": debt_ratio,
            "color": (
                GREEN if debt_ratio <= 0.5 else YELLOW if debt_ratio <= 0.6 else RED
            ),
        }
        ratios["debt_to_equity_ratio"] = {
            "value": debt_to_equity_ratio,
            "color": (
                GREEN
                if debt_to_equity_ratio <= 0.7
                else YELLOW if debt_to_equity_ratio <= 1 else RED
            ),
        }
        ratios["interest_coverage_ratio"] = {
            "value": interest_coverage_ratio,
            "color": (
                GREEN
                if interest_coverage_ratio >= 3
                else YELLOW if interest_coverage_ratio >= 1.5 else RED
            ),
        }
        ratios["debt_service_coverage_ratio"] = {
            "value": debt_service_coverage_ratio,
            "color": (
                GREEN
                if debt_service_coverage_ratio >= 1
                else YELLOW if debt_service_coverage_ratio >= 0.5 else RED
            ),
        }

    # Efficiency Ratios
    if total_assets != 0:
        asset_turnover_ratio = round(net_sales / total_assets, 2)
        inventory_turnover_ratio = (
            round(cost_of_goods_sold / inventory, 2) if inventory != 0 else 0
        )
        days_sales_in_inventory_ratio = (
            round(365 / inventory_turnover_ratio, 2)
            if inventory_turnover_ratio != 0
            else 0
        )

        ratios["asset_turnover_ratio"] = {
            "value": asset_turnover_ratio,
            "color": (
                GREEN
                if asset_turnover_ratio >= 1
                else YELLOW if asset_turnover_ratio >= 0.5 else RED
            ),
        }
        ratios["inventory_turnover_ratio"] = {
            "value": inventory_turnover_ratio,
            "color": (
                GREEN
                if inventory_turnover_ratio >= 6
                else YELLOW if inventory_turnover_ratio >= 3 else RED
            ),
        }
        ratios["days_sales_in_inventory_ratio"] = {
            "value": days_sales_in_inventory_ratio,
            "color": (
                GREEN
                if days_sales_in_inventory_ratio <= 60
                else YELLOW if days_sales_in_inventory_ratio <= 120 else RED
            ),
        }

    if shareholder_equity != 0:
        receivables_turnover_ratio = (
            round(net_credit_sales / average_accounts_receivable, 2)
            if average_accounts_receivable != 0
            else 0
        )

        ratios["receivables_turnover_ratio"] = {
            "value": receivables_turnover_ratio,
            "color": (
                GREEN
                if receivables_turnover_ratio >= 10
                else YELLOW if receivables_turnover_ratio >= 7 else RED
            ),
        }

    # Profitability Ratios
    if net_sales != 0:
        gross_margin_ratio = round(gross_profit / net_sales, 2)
        operating_margin_ratio = round(operating_income / net_sales, 2)

        ratios["gross_margin_ratio"] = {
            "value": gross_margin_ratio,
            "color": (
                GREEN
                if gross_margin_ratio >= 0.4
                else YELLOW if gross_margin_ratio >= 0.2 else RED
            ),
        }
        ratios["operating_margin_ratio"] = {
            "value": operating_margin_ratio,
            "color": (
                GREEN
                if operating_margin_ratio >= 0.15
                else YELLOW if operating_margin_ratio >= 0.05 else RED
            ),
        }

    if total_assets != 0:
        return_on_assets_ratio = round(net_income / total_assets, 2)
        ratios["return_on_assets_ratio"] = {
            "value": return_on_assets_ratio,
            "color": (
                GREEN
                if return_on_assets_ratio >= 0.03
                else YELLOW if return_on_assets_ratio >= 0.01 else RED
            ),
        }

    if shareholder_equity != 0:
        return_on_equity_ratio = round(net_income / shareholder_equity, 2)

        ratios["return_on_equity_ratio"] = {
            "value": return_on_equity_ratio,
            "color": (
                GREEN
                if return_on_equity_ratio >= 0.1
                else YELLOW if return_on_equity_ratio >= 0.05 else RED
            ),
        }

    return ratios


def journal_entry_data(request):
    # Retrieve pending journal entries
    pending_entries = JournalEntry.objects.filter(status="Pending")
    print(pending_entries)
    # Return the QuerySet directly
    return pending_entries


def home(request):
    """
    Renders the home page with financial ratios.
    """
    pending_entries = journal_entry_data(request)
    ratios = calculate_ratios()  # Call the function to get the ratios
    context = {
        "ratios": ratios,
        "pending_entries": pending_entries,
    }
    return render(request, "main_page/home.html", context)

def email_report(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            subject = form.cleaned_data.get("subject")
            from_email=settings.DEFAULT_FROM_EMAIL,
            message = request.POST.get('document.Body')

            full_message = f"""
                Received message below from {email}, {subject}
                ________________________
                {message}
                """
            msg = EmailMultiAlternatives(subject, full_message, email, ["myin1@students.kennesaw.edu"])
            msg.attach_alternative('document.pdf', message, 'application/pdf')
            msg.send()
    form = ContactForm()
    return HttpResponse("Email sent successfully!")
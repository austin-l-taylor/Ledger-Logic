from django.urls import path
from . import views

urlpatterns = [
    # ----------------------- User authentication URLs -------------------------------- #
    path("", views.login_user, name="login"),  # Login page
    path("logout/", views.logout_user, name="logout"),  # Logout action
    path("register/", views.register_user, name="register"),  # Registration page
    path(
        "forgot_password/", views.forgot_password, name="forgot_password"
    ),  # Password recovery page
    path("question/", views.question, name="question"),  # Security question page
    path(
        "reset_password/", views.reset_password, name="reset_password"
    ),  # Password reset page
    path("home/", views.home, name="home"),  # Home page
    path(
        "send-email/<int:user_id>/", views.send_email_view, name="send_email"
    ),  # Send email action
    path(
        "activate/<uidb64>/<token>/", views.activate, name="activate"
    ),  # Account activation action
    # ----------------------- Chart of Accounts URLs -------------------------------- #
    path(
        "chart-of-accounts/", views.chart_of_accounts, name="chart_of_accounts"
    ),  # Chart of Accounts page
    path(
        "account/deactivate/<int:account_id>/",
        views.deactivate_account,
        name="deactivate_account",
    ),  # Deactivate account action
    path(
        "account/activate/<int:account_id>/",
        views.activate_account,
        name="activate_account",
    ),  # Activate account action
    path("account/add/", views.add_account, name="add_account"),  # Add account page
    path(
        "account/edit/<int:account_id>/", views.edit_account, name="edit_account"
    ),  # Edit account page
    path(
        "ledger/<int:account_id>/", views.ledger, name="ledger"
    ),  # Ledger page for a specific account
    path(
        "view-coa-logs/", views.view_coa_logs, name="view_coa_logs"
    ),  # View Chart of Accounts logs page
    # ----------------------- Other URLs -------------------------------- #
    path("help/", views.help, name="help"),  # Help page
    path(
        "journal-entries/", views.journal_entry_page, name="journal_entry_page"
    ),  # Journal entries page
    path(
        "journal-entry/add/", views.add_journal_entry, name="add_journal_entry"
    ),  # Add journal entry page
    path(
        "entry_details/<int:entry_id>/", views.entry_details, name="entry_details"
    ),  # Journal entry details page
    path("contact/", views.email, name="contact"),  # Contact page
    path(
        "addComment/<str:account_name>", views.add_comment, name="addComment"
    ),  # Add comment action
    # ----------------------- Financial Statement URLs -------------------------------- #
    path(
        "trial-balance/", views.trial_balance, name="trial_balance"
    ),  # Trial balance page
    path(
        "income-statement/", views.income_statement, name="income_statement"
    ),  # Income statement page
    path(
        "balance-sheet/", views.balance_sheet, name="balance_sheet"
    ),  # Balance sheet page
    path(
        "retained-earnings/", views.retained_earnings, name="retained_earnings"
    ),  # Retained earnings page
    # ----------------------- Export Email URLs -------------------------------- #
    path(
        "export_to_pdf/", views.export_to_pdf, name="export_to_pdf"
    ),  # Export to PDF action
    path(
        "email_report/", views.email_report, name="email_report"
    ),  # Email report action
]

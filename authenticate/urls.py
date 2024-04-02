from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("register/", views.register_user, name="register"),
    path("forgot_password/", views.forgot_password, name="forgot_password"),
    path("question/", views.question, name="question"),
    path("reset_password/", views.reset_password, name="reset_password"),
    path("home/", views.home, name="home"),
    path("send-email/<int:user_id>/", views.send_email_view, name="send_email"),
    path("activate/<uidb64>/<token>/", views.activate, name="activate"),
    path("chart-of-accounts/", views.chart_of_accounts, name="chart_of_accounts"),
    path(
        "account/deactivate/<int:account_id>/",
        views.deactivate_account,
        name="deactivate_account",
    ),
    path(
        "account/activate/<int:account_id>/",
        views.activate_account,
        name="activate_account",
    ),
    path("account/add/", views.add_account, name="add_account"),
    path("account/edit/<int:account_id>/", views.edit_account, name="edit_account"),
    path("ledger/<int:account_id>/", views.ledger, name="ledger"),
    path("view-coa-logs/", views.view_coa_logs, name="view_coa_logs"),
    path("help/", views.help, name="help"),
    path("journal-entries/", views.journal_entry_page, name="journal_entry_page"),
    path("journal-entry/add/", views.add_journal_entry, name="add_journal_entry"),
    path('entry_details/<int:entry_id>/', views.entry_details, name='entry_details'),
]

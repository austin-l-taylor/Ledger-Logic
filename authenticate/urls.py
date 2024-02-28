from django.urls import path
from . import views
from .views import send_email_view, chart_of_accounts, deactivate_account, activate_account, add_account

urlpatterns = [
    path("", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("register/", views.register_user, name="register"),
    path("forgot_password/", views.forgot_password, name="forgot_password"),
    path("question/", views.question, name="question"),
    path("reset_password/", views.reset_password, name="reset_password"),
    path("home/", views.home, name="home"),
    path('send-email/<int:user_id>/', send_email_view, name='send_email'),
    path('activate/<uidb64>/<token>/', views.activate, name= 'activate'),
    path('chart-of-accounts/', chart_of_accounts, name='chart_of_accounts'),
    path('account/deactivate/<int:account_id>/', deactivate_account, name='deactivate_account'),
    path('account/activate/<int:account_id>/', activate_account, name='activate_account'),
    path('account/add/', add_account, name='add_account'),
    path('account/edit/<int:account_id>/', views.edit_account, name='edit_account'),
     path("help/", views.help, name="help"),
]

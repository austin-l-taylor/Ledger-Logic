from django.urls import path
from . import views
from .views import send_email_view

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
]

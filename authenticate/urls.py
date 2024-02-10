from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("register/", views.register_user, name="register"),
    path("forgot_password/", views.forgot_password, name="forgot_password"),
    path("question/", views.question, name="question"),
    path("home/", views.home, name="home"),
]

from django.urls import path
from django.contrib.auth.views import (
    LogoutView, LoginView, PasswordResetView, PasswordChangeView,
)

from . import views

app_name = 'users'

urlpatterns = [
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('logout/', LogoutView.as_view(
        template_name='users/logged_out.html'), name='logout'),
    path('login/', LoginView.as_view(template_name='users/login.html'),
         name='login'),
    path('password_reset_form/', PasswordResetView.as_view(
        template_name='users/password_reset_form.html'),
        name='password_reset_form'),
    path('password_change/', PasswordChangeView.as_view(
        template_name='users/password_change_form.html'),
        name='password_change_form'),
    path('password_change/done/', PasswordChangeView.as_view(
        template_name='users/password_change_done.html'),
        name='password_change_done')
]

from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from .views import (
    GoogleLoginRedirectApi,
    GoogleLoginApi,
    password_reset,
    confirm_password_reset, UserRegistrationApi, LoginApi,
)

app_name = "user"


urlpatterns = [
    path('register/', UserRegistrationApi.as_view(), name='register'),
    path('login/', LoginApi.as_view(), name='login'),
    path(
        "google-redirect/",
        csrf_exempt(GoogleLoginRedirectApi.as_view()),
        name="google-redirect",
    ),
    path("google-login/", csrf_exempt(GoogleLoginApi.as_view()), name="google-login"),
    path("password-reset/", csrf_exempt(password_reset), name="password-reset"),
    path(
        "password-reset/confirm/<uidb64>/<token>/",
        csrf_exempt(confirm_password_reset),
        name="confirm_password_reset",
    ),
]

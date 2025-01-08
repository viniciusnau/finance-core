import os
import json

from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt
from rest_framework import serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegistrationSerializer, LoginSerializer
from .services import GoogleRawLoginFlowService, generate_secure_password


@csrf_exempt
def password_reset(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        if email:
            user = get_object_or_404(User, email=email)
            token = default_token_generator.make_token(user)
            user.password_reset_token = token
            user.save()

            protocol = "https" if request.is_secure() else "http"
            domain = request.META["HTTP_HOST"]
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = reverse(
                "user:confirm_password_reset",
                kwargs={
                    "uidb64": uidb64,
                    "token": token,
                },
            )

            context = {
                "user": user,
                "protocol": protocol,
                "domain": domain,
                "reset_url": reset_url,
            }
            email_html = render_to_string("password_reset.html", context)
            email_text = strip_tags(email_html)

            subject = "Alterar Senha"
            from_email = os.environ.get("EMAIL_HOST_USER")
            recipient_list = [email]

            email = EmailMultiAlternatives(
                subject=subject,
                body=email_text,
                from_email=from_email,
                to=recipient_list,
                reply_to=[from_email],
            )

            email.attach_alternative(email_html, "text/html")
            email.send()
            return JsonResponse({"message": "Password reset email sent."})

    return JsonResponse({"message": "Invalid request."}, status=400)


@csrf_exempt
def confirm_password_reset(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        if request.method == "POST":
            password = request.POST.get("password")
            confirm_password = request.POST.get("confirm_password")
            if password == confirm_password:
                user.set_password(password)
                user.password_reset_token = None
                user.save()
                login(request, user)
                messages.success(request, "Your password has been successfully reset.")
                return render(
                    request,
                    "success.html",
                    {"message": "Your password has been successfully reset."},
                )
            else:
                messages.error(request, "Passwords do not match.")
                return render(
                    request, "error.html", {"message": "Passwords do not match."}
                )
        return render(request, "confirm_reset_password.html", {"valid_link": True})
    else:
        return render(
            request,
            "error.html",
            {"message": "The password reset link is invalid."},
        )


class PublicApi(APIView):
    authentication_classes = ()
    permission_classes = ()


class GoogleLoginRedirectApi(PublicApi):
    def get(self, request, *args, **kwargs):
        google_login_flow = GoogleRawLoginFlowService()

        authorization_url, state = google_login_flow.get_authorization_url()

        request.session["google_oauth2_state"] = state

        return redirect(authorization_url)


class GoogleLoginApi(PublicApi):
    class InputSerializer(serializers.Serializer):
        code = serializers.CharField(required=False)
        error = serializers.CharField(required=False)
        state = serializers.CharField(required=False)

    def get(self, request, *args, **kwargs):
        input_serializer = self.InputSerializer(data=request.GET)
        input_serializer.is_valid(raise_exception=True)

        validated_data = input_serializer.validated_data

        code = validated_data.get("code")
        error = validated_data.get("error")
        state = validated_data.get("state")

        if error is not None:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        if code is None or state is None:
            return Response(
                {"error": "Code and state are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session_state = request.session.get("google_oauth2_state")

        if session_state is None:
            return Response(
                {"error": "CSRF check failed."}, status=status.HTTP_400_BAD_REQUEST
            )

        del request.session["google_oauth2_state"]

        if state != session_state:
            return Response(
                {"error": "CSRF check failed."}, status=status.HTTP_400_BAD_REQUEST
            )

        google_login_flow = GoogleRawLoginFlowService()

        google_tokens = google_login_flow.get_tokens(code=code)

        id_token_decoded = google_tokens.decode_id_token()

        user_email = id_token_decoded["email"]

        try:
            user = User.objects.get(email=user_email)
        except ObjectDoesNotExist:
            password = generate_secure_password()
            user = User.objects.create_user(
                username=user_email,
                email=user_email,
                password=password
            )
            context = {
                "user": user,
                "password": password
            }
            email_html = render_to_string("register.html", context)
            email_text = strip_tags(email_html)

            subject = "Cadastro realizado com sucesso!"
            from_email = os.environ.get("EMAIL_HOST_USER")
            recipient_list = [user_email]

            email = EmailMultiAlternatives(
                subject=subject,
                body=email_text,
                from_email=from_email,
                to=recipient_list,
                reply_to=[from_email],
            )

            email.attach_alternative(email_html, "text/html")
            email.send()

        token, created = Token.objects.get_or_create(user=user)
        api_token = token.key

        try:
            logged_user = Token.objects.get(key=api_token).user

            if logged_user:
                url = f"{os.environ.get('GOOGLE_REDIRECT_URL')}/?google_token={api_token}&user_id={logged_user.id}"
                return redirect(url)

            else:
                return Response({"error": "Access Denied"}, status=status.HTTP_403_FORBIDDEN)

        except Token.DoesNotExist:
            return Response({"error": "Invalid API token."}, status=status.HTTP_400_BAD_REQUEST)


class UserRegistrationApi(APIView):
    def post(self, request, *args, **kwargs):
        serializer = RegistrationSerializer(data=request.data)
        try:
            if serializer.is_valid(raise_exception=True):
                user = serializer.save()
                context = {'user': user.username}
                email_html = render_to_string("register.html", context)
                email_text = strip_tags(email_html)
                subject = "Bem Vindo(a)!"
                from_email = os.environ.get("EMAIL_HOST_USER")
                recipient_list = [user.email]
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=email_text,
                    from_email=from_email,
                    to=recipient_list,
                    reply_to=[from_email],
                )
                email.attach_alternative(email_html, "text/html")
                email.send()
                return Response(
                    {"message": "User registered successfully. A confirmation email has been sent."},
                    status=status.HTTP_201_CREATED,
                )
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginApi(APIView):
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = authenticate(username=username, password=password)

            if user is not None:
                token, created = Token.objects.get_or_create(user=user)
                return Response(
                    {"message": "Login successful", "token": token.key, "username": username},
                    status=status.HTTP_200_OK
                )
            else:
                raise AuthenticationFailed("Invalid credentials")

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

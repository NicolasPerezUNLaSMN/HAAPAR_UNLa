from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import BadHeaderError, send_mail
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from haapar_unla_app.forms import SignUpForm

User = get_user_model()


# ---------------------------
# FORMULARIO PERFIL
# ---------------------------
class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]


# ---------------------------
# AUTENTICACIÓN
# ---------------------------
def registro(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip().lower()

        existing = User.objects.filter(
            Q(username__iexact=username) | Q(email__iexact=email)
        ).first()
        if existing and not existing.is_active:
            current_site = get_current_site(request)
            uid = urlsafe_base64_encode(force_bytes(existing.pk))
            token = default_token_generator.make_token(existing)
            reactivate_link = request.build_absolute_uri(
                reverse("reactivar-cuenta", kwargs={"uidb64": uid, "token": token})
            )
            subject = "Reactivar tu cuenta"
            message = render_to_string(
                "haapar_unla_app/autenticacion/reactivar_cuenta_email.txt",
                {
                    "user": existing,
                    "reactivate_link": reactivate_link,
                    "domain": current_site.domain,
                },
            )
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [existing.email],
                    fail_silently=False,
                )
                messages.info(
                    request,
                    "Hemos enviado un email para reactivar tu cuenta. Revisa tu bandeja de entrada.",
                )
            except BadHeaderError:
                messages.error(request, "Error al enviar el email de reactivación.")
            form = SignUpForm()
            return render(
                request, "haapar_unla_app/autenticacion/signup.html", {"form": form}
            )

        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("inicio")
    else:
        form = SignUpForm()
    return render(request, "haapar_unla_app/autenticacion/signup.html", {"form": form})


def reactivar_cuenta(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                user.first_name = request.POST.get("first_name", user.first_name)
                user.last_name = request.POST.get("last_name", user.last_name)
                user.is_active = True
                user.save()
                login(request, user)
                messages.success(request, "Cuenta reactivada correctamente.")
                return redirect("inicio")
        else:
            form = SetPasswordForm(user)
        return render(
            request,
            "haapar_unla_app/autenticacion/reactivar_cuenta.html",
            {"form": form, "reactivate_user": user},
        )
    else:
        messages.error(request, "El enlace de reactivación no es válido o ha expirado.")
        return redirect("sign-up")


def cerrar_sesion(request):
    logout(request)
    return redirect("inicio")


def iniciar_sesion(request):
    if request.method == "GET":
        return render(
            request,
            "haapar_unla_app/autenticacion/signin.html",
            {"form": AuthenticationForm()},
        )
    else:
        user = authenticate(
            request,
            username=request.POST["username"],
            password=request.POST["password"],
        )
        if user is None:
            return render(
                request,
                "haapar_unla_app/autenticacion/signin.html",
                {
                    "form": AuthenticationForm(),
                    "error": "El usuario o la contraseña son incorrectas.",
                },
            )
        login(request, user)
        return redirect("inicio")


# ---------------------------
# PERFIL
# ---------------------------
@login_required
def perfil(request):
    user = request.user
    form = ProfileForm(instance=user)
    pass_form = PasswordChangeForm(user)

    if request.method == "POST":
        if "update_profile" in request.POST:
            form = ProfileForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, "Perfil actualizado correctamente.")
                return redirect("perfil")

        elif "change_password" in request.POST:
            pass_form = PasswordChangeForm(user, request.POST)
            if pass_form.is_valid():
                user = pass_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Contraseña cambiada con éxito.")
                return redirect("perfil")
            else:
                messages.error(
                    request,
                    "No se pudo cambiar la contraseña. Revisa los errores del formulario.",
                )

        elif "delete_profile" in request.POST:
            user.is_active = False
            user.save()
            messages.error(request, "Tu cuenta fue desactivada correctamente.")
            logout(request)
            return redirect("inicio")

    initials = (
        (user.first_name[:1] + user.last_name[:1]).upper()
        if user.first_name and user.last_name
        else user.username[:2].upper()
    )
    return render(
        request,
        "haapar_unla_app/perfil.html",
        {
            "form": form,
            "pass_form": pass_form,
            "initials": initials,
        },
    )


# ---------------------------
# PASSWORD RESET
# ---------------------------
def password_reset_request(request):
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data["email"]
            associated_users = User.objects.filter(email=data)
            if associated_users.exists():
                for user in associated_users:
                    subject = "Restablecimiento de Contraseña Solicitado"
                    email_template_name = (
                        "haapar_unla_app/autenticacion/password_reset_email.txt"
                    )
                    c = {
                        "email": user.email,
                        "domain": get_current_site(request).domain,
                        "site_name": "HAAPAR UNLA",
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        "token": default_token_generator.make_token(user),
                        "protocol": "http",
                    }
                    email_message = render_to_string(email_template_name, c)
                    try:
                        send_mail(
                            subject,
                            email_message,
                            "admin@example.com",
                            [user.email],
                            fail_silently=False,
                        )
                    except BadHeaderError:
                        return HttpResponse("Invalid header found.")
                messages.success(
                    request,
                    "Se ha enviado un correo con las instrucciones para restablecer su contraseña.",
                )
                return redirect("password-reset-done")
            messages.error(request, "El correo electrónico no está registrado.")
    password_reset_form = PasswordResetForm()
    return render(
        request,
        "haapar_unla_app/autenticacion/password_reset.html",
        {"password_reset_form": password_reset_form},
    )


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(
                    request,
                    "Tu contraseña ha sido restablecida. Ya puedes iniciar sesión.",
                )
                return redirect("password-reset-complete")
        else:
            form = SetPasswordForm(user)
        return render(
            request,
            "haapar_unla_app/autenticacion/password_reset_confirm.html",
            {"form": form},
        )
    else:
        messages.error(
            request, "El enlace de restablecimiento es inválido o ha expirado."
        )
        return redirect("password-reset-request")


def password_reset_done(request):
    return render(request, "haapar_unla_app/autenticacion/password_reset_done.html")


def password_reset_complete(request):
    return render(request, "haapar_unla_app/autenticacion/password_reset_complete.html")

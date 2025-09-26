from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from haapar_unla_app.models import Tema, Variable, Subsistema, Actor, TendenciaExterna
#from django.contrib.auth.models import User
from .forms import SignUpForm
from django.contrib import messages
from django import forms
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from django.template.loader import render_to_string
from django.core.mail import send_mail, BadHeaderError
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse
from django.db.models import Count, Q

User = get_user_model()

# ---------------------------
# FORMULARIO PERFIL
# ---------------------------
class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


# ---------------------------
# PROYECTOS
# ---------------------------
def inicio(request):
    return render(request, 'haapar_unla_app/crear-reporte.html')


@login_required
def listar_proyectos(request):
    temas = Tema.objects.filter(user=request.user, activo=True)
    return render(request, 'haapar_unla_app/listar-proyectos.html', {'temas': temas})


def proyecto_detalle(request, tema_id):
    tema = get_object_or_404(Tema, id_tema=tema_id)
    return render(request, 'haapar_unla_app/proyecto-detalle.html', {'tema': tema})


@login_required
def crear_reporte(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        horizonte = request.POST.get('horizonte')
        territorio = request.POST.get('territorio')

        Tema.objects.create(
            user=request.user,
            nombre=nombre,
            descripcion=descripcion,
            horizonte=horizonte,
            territorio=territorio
        )
        return redirect('crear-reporte')
    return render(request, 'haapar_unla_app/crear-reporte.html')


@login_required
def eliminar_proyecto(request, id_tema):
    tema = get_object_or_404(Tema, id_tema=id_tema, user=request.user)
    if request.method == 'POST':
        tema.activo = False
        tema.save()
        return redirect('listar_proyectos')
    return render(request, 'haapar_unla_app/eliminar-proyecto-confirmacion.html', {'tema': tema})


# ---------------------------
# VARIABLES
# ---------------------------
def variable_detalle(request):
    variables = Variable.objects.filter(activo=True)
    return render(request, 'haapar_unla_app/variable-detalle.html', {"variables": variables})


def eliminar_variable(request, pk):
    variable = get_object_or_404(Variable, pk=pk)
    variable.activo = False
    variable.save()
    return redirect("variable_detalle")


def editar_variable(request, pk):
    variable = get_object_or_404(Variable, pk=pk)
    if request.method == "POST":
        variable.nombre = request.POST.get("nombre")
        variable.nombre_corto = request.POST.get("nombre_corto")
        variable.descripcion = request.POST.get("descripcion")
        variable.save()
        return redirect("variable_detalle")
    return render(request, "haapar_unla_app/editar-variable.html", {"variable": variable})


def crear_variable(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        nombre_corto = request.POST.get("nombre_corto")
        descripcion = request.POST.get("descripcion")
        tipo = request.POST.get("tipo")

        subsistema = Subsistema.objects.first()

        Variable.objects.create(
            nombre=nombre,
            nombre_corto=nombre_corto,
            descripcion=descripcion,
            tipo=tipo,
            subsistema=subsistema
        )
        return redirect("variable_detalle")
    return render(request, "haapar_unla_app/crear-variable.html")


# ---------------------------
# SUBSISTEMAS
# ---------------------------
def subsistemas(request):
    tema = request.session.get('reporte_tema', 'TEMA NO ESPECIFICADO')
    anio = request.session.get('reporte_anio', '')
    grado = request.session.get('reporte_grado', '')

    if request.method == 'GET':
        tema = request.GET.get('tema', tema)
        anio = request.GET.get('anio', anio)
        grado = request.GET.get('grado', grado)
        request.session['reporte_tema'] = tema
        request.session['reporte_anio'] = anio
        request.session['reporte_grado'] = grado

    return render(request, 'haapar_unla_app/subsistemas.html', {'tema': tema, 'anio': anio, 'grado': grado})

"""
def subsistemas(request):
    if request.method == 'GET':
        tema = request.GET.get('tema', request.session.get('reporte_tema', 'TEMA NO ESPECIFICADO'))
        anio = request.GET.get('anio', request.session.get('reporte_anio', ''))
        grado = request.GET.get('grado', request.session.get('reporte_grado', ''))

        request.session['reporte_tema'] = tema
        request.session['reporte_anio'] = anio
        request.session['reporte_grado'] = grado

    return render(request, 'haapar_unla_app/subsistemas.html', {
        'tema': tema,
        'anio': anio,
        'grado': grado
    }) 
"""


# ---------------------------
# AUTENTICACIÓN
# ---------------------------
def registro(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("inicio")
        else:
            return render(request, 'haapar_unla_app/autenticacion/signup.html', {
                'form': form,
            })
    else:
        form = SignUpForm()
        return render(request, 'haapar_unla_app/autenticacion/signup.html', {
            'form': form
        })


def cerrar_sesion(request):
    logout(request)
    return redirect("inicio")


def iniciar_sesion(request):
    if request.method == 'GET':
        return render(request, "haapar_unla_app/autenticacion/signin.html", {
            'form': AuthenticationForm()
        })
    else:
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, "haapar_unla_app/autenticacion/signin.html", {
                'form': AuthenticationForm(),
                'error': 'El usuario o la contraseña son incorrectas.'
            })
        else:
            login(request, user)
            return redirect('inicio')


# ---------------------------
# PERFIL
# ---------------------------
@login_required
def perfil(request):
    user = request.user

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            form = ProfileForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Perfil actualizado correctamente.')
                return redirect('perfil')

        elif 'change_password' in request.POST:
            pass_form = PasswordChangeForm(user, request.POST)
            if pass_form.is_valid():
                user = pass_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Contraseña cambiada con éxito.')
                return redirect('perfil')

        elif 'delete_profile' in request.POST:
            user.is_active = False
            user.save()
            messages.success(request, "Tu cuenta fue desactivada correctamente.")
            logout(request)
            return redirect("inicio")

    else:
        form = ProfileForm(instance=user)
        pass_form = PasswordChangeForm(user)

    initials = (user.first_name[:1] + user.last_name[:1]).upper() if user.first_name and user.last_name else user.username[:2].upper()

    return render(request, 'haapar_unla_app/perfil.html', {
        'form': form,
        'pass_form': pass_form,
        'initials': initials,
    })


# ---------------------------
# ERRORES
# ---------------------------
def error_400_view(request, exception):
    return render(request, 'haapar_unla_app/error/400.html', status=400)


def error_403_view(request, exception):
    return render(request, 'haapar_unla_app/error/403.html', status=403)


def error_404_view(request, exception):
    return render(request, 'haapar_unla_app/error/404.html', status=404)


def error_500_view(request):
    return render(request, 'haapar_unla_app/error/500.html', status=500)


# ---------------------------
# ACTORES
# ---------------------------
def actor_detalle(request, tema_id):
    tema = get_object_or_404(Tema, id_tema=tema_id)
    actores = Actor.objects.filter(tema=tema, activo=True)
    return render(request, 'haapar_unla_app/actor-detalle.html', {
        'tema': tema,
        'actores': actores
    })


def crear_actor(request, tema_id):
    tema = get_object_or_404(Tema, id_tema=tema_id)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        puesto = request.POST.get('puesto')
        subsistema_id = request.POST.get('subsistema')
        emite = 'emite' in request.POST
        recibe = 'recibe' in request.POST
        influencia = request.POST.get('influencia')

        subsistema = get_object_or_404(Subsistema, id_subsistema=subsistema_id)

        Actor.objects.create(
            tema=tema,
            subsistema=subsistema,
            nombre=nombre,
            descripcion=descripcion,
            puesto=puesto,
            emite=emite,
            recibe=recibe,
            influencia=influencia
        )
        return redirect('actor_detalle', tema_id=tema_id)

    subsistemas = Subsistema.objects.filter(activo=True)
    return render(request, 'haapar_unla_app/crear-actor.html', {
        'tema': tema,
        'subsistemas': subsistemas
    })


def editar_actor(request, pk):
    actor = get_object_or_404(Actor, pk=pk)
    if request.method == 'POST':
        actor.nombre = request.POST.get('nombre')
        actor.descripcion = request.POST.get('descripcion')
        actor.puesto = request.POST.get('puesto')
        actor.emite = 'emite' in request.POST
        actor.recibe = 'recibe' in request.POST
        actor.influencia = request.POST.get('influencia')
        actor.save()

        return redirect('actor_detalle', tema_id=actor.tema.id_tema)

    subsistemas = Subsistema.objects.filter(activo=True)
    return render(request, 'haapar_unla_app/editar-actor.html', {
        'actor': actor,
        'subsistemas': subsistemas
    })


def eliminar_actor(request, pk):
    actor = get_object_or_404(Actor, pk=pk)
    tema_id = actor.tema.id_tema
    actor.activo = False
    actor.save()
    return redirect('actor_detalle', tema_id=tema_id)


# ---------------------------
# TENDENCIAS
# ---------------------------
@login_required
def listar_tendencias(request):
    tendencias_por_subsistema = Subsistema.objects.annotate(
        num_tendencias=Count('tendenciaexterna', filter=Q(tendenciaexterna__activo=True), distinct=True)
    ).filter(num_tendencias__gt=0)

    todas_las_tendencias = TendenciaExterna.objects.filter(activo=True)

    context = {
        'tendencias_por_subsistema': tendencias_por_subsistema,
        'todas_las_tendencias': todas_las_tendencias,
    }

    return render(request, 'haapar_unla_app/tendencias.html', context)


@login_required
def tendencia_detalle(request, tema_id):
    tema = get_object_or_404(Tema, id_tema=tema_id)
    tendencias = TendenciaExterna.objects.filter(tema=tema, activo=True)
    return render(request, 'haapar_unla_app/tendencia-detalle.html', {
        'tema': tema,
        'tendencias': tendencias
    })


@login_required
def crear_tendencia(request, tema_id):
    tema = get_object_or_404(Tema, id_tema=tema_id)
    subsistemas = Subsistema.objects.filter(activo=True)

    if request.method == 'POST':
        subsistema_id = request.POST.get('subsistema')
        subsistema = get_object_or_404(Subsistema, id_subsistema=subsistema_id)

        nombre = request.POST.get('nombre')
        nombre_corto = request.POST.get('nombre_corto')
        descripcion = request.POST.get('descripcion')

        TendenciaExterna.objects.create(
            tema=tema,
            subsistema=subsistema,
            nombre=nombre,
            nombre_corto=nombre_corto,
        )

        return redirect('tendencia_detalle', tema_id=tema.id_tema)

    context = {
        'tema': tema,
        'subsistemas': subsistemas,
    }
    return render(request, 'haapar_unla_app/crear-tendencia.html', context)


@login_required
def editar_tendencia(request, pk):
    tendencia = get_object_or_404(TendenciaExterna, pk=pk)
    if request.method == 'POST':
        tendencia.nombre = request.POST.get('nombre')
        tendencia.descripcion = request.POST.get('descripcion')
        tendencia.save()
        return redirect('tendencia_detalle', tema_id=tendencia.tema.id_tema)

    subsistemas = Subsistema.objects.filter(activo=True)
    return render(request, 'haapar_unla_app/editar-tendencia.html', {
        'tendencia': tendencia,
        'subsistemas': subsistemas
    })


@login_required
def eliminar_tendencia(request, pk):
    tendencia = get_object_or_404(TendenciaExterna, pk=pk)
    tema_id = tendencia.tema.id_tema
    tendencia.activo = False
    tendencia.save()
    return redirect('tendencia_detalle', tema_id=tema_id)


# ---------------------------
# PASSWORD RESET
# ---------------------------
def password_reset_request(request):
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = User.objects.filter(email=data)
            if associated_users.exists():
                for user in associated_users:
                    subject = "Restablecimiento de Contraseña Solicitado"
                    email_template_name = "haapar_unla_app/autenticacion/password_reset_email.txt"
                    c = {
                        "email": user.email,
                        'domain': get_current_site(request).domain,
                        'site_name': 'HAAPAR UNLA',
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'http',
                    }
                    email_message = render_to_string(email_template_name, c)
                    try:
                        send_mail(subject, email_message, 'admin@example.com', [user.email], fail_silently=False)
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.')
                messages.success(request, 'Se ha enviado un correo con las instrucciones para restablecer su contraseña.')
                return redirect('password_reset_done')
            messages.error(request, 'El correo electrónico no está registrado.')
    password_reset_form = PasswordResetForm()
    return render(request, "haapar_unla_app/autenticacion/password_reset.html", {"password_reset_form": password_reset_form})


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Tu contraseña ha sido restablecida. Ya puedes iniciar sesión.')
                return redirect('password_reset_complete')
        else:
            form = SetPasswordForm(user)
        return render(request, 'haapar_unla_app/autenticacion/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, 'El enlace de restablecimiento es inválido o ha expirado.')
        return redirect('password_reset_request')


def password_reset_done(request):
    return render(request, 'haapar_unla_app/autenticacion/password_reset_done.html')


def password_reset_complete(request):
    return render(request, 'haapar_unla_app/autenticacion/password_reset_complete.html')

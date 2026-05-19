from .services.ai_client import generar_respuesta_llm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import (
    AuthenticationForm, PasswordChangeForm,
    PasswordResetForm, SetPasswordForm
)
from django.contrib.auth import (
    login, logout, authenticate,
    update_session_auth_hash, get_user_model
)
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from django.template.loader import render_to_string
from django.core.mail import send_mail, BadHeaderError
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse, JsonResponse
from django.db.models import Prefetch, Count, Q
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Tema

import json  
from django.http import HttpResponseForbidden
from django.contrib.auth.models import Group
from .services.ia_service import generar_estructura_prospectiva
from .forms import SignUpForm
from django.contrib.auth.models import Group
# Imports limpios
from haapar_unla_app.models import (
    Tema, Sistema, Subsistema, Variable,
    Historial, TendenciaExterna, ActorClave, RelacionActor,
    Influencia, PESTEL, EvaluacionVariable
)

User = get_user_model()

# ---------------------------
# FORMULARIO PERFIL
# ---------------------------
class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

# ---------------------------
# INICIO
# ---------------------------

def inicio(request):
    return render(request, 'haapar_unla_app/crear-reporte.html')


# ---------------------------
# PROYECTOS
# ---------------------------
@login_required
def crear_reporte(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        horizonte = request.POST.get("horizonte")
        territorio = request.POST.get("territorio")

        tema = Tema.objects.create(
            user=request.user,
            nombre=nombre,
            descripcion=descripcion,
            horizonte=horizonte,
            territorio=territorio
        )

        # 1. Crea la estructura (Variables, Tendencias, Actores)
        generar_estructura_prospectiva(tema)
        
        # 2. Crea la matriz matemática lógica con la IA
        from haapar_unla_app.services.ia_service import generar_evaluaciones_e_influencias
        generar_evaluaciones_e_influencias(tema, request.user)

        return redirect("subsistemas", tema_id=tema.id_tema)


@login_required
def listar_proyectos(request):
    # Proyectos creados por el usuario
    propios = Tema.objects.filter(user=request.user, activo=True)
    # Proyectos donde el usuario es colaborador
    colaborando = Tema.objects.filter(colaboradores=request.user, activo=True)

    # Unir ambos conjuntos y evitar duplicados
    temas = propios | colaborando

    return render(request, 'haapar_unla_app/listar-proyectos.html', {
        'temas': temas.distinct()
    })



@login_required
def proyecto_detalle(request, tema_id, subsistema_id=None):
    tema = get_object_or_404(Tema, pk=tema_id, activo=True)
    subsistema, subsistemas, variables = None, None, []

    if subsistema_id:
        subsistema = get_object_or_404(Subsistema, pk=subsistema_id, activo=True)
        variables = Variable.objects.filter(subsistema=subsistema, activo=True)
    else:
        subsistemas = Subsistema.objects.filter(sistema__tema=tema, activo=True)

    return render(request, "haapar_unla_app/proyecto-detalle.html", {
        "tema": tema,
        "subsistema": subsistema,
        "subsistemas": subsistemas,
        "variables": variables,
    })


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
@login_required
def variable_detalle(request, subsistema_id):
    subsistema = get_object_or_404(Subsistema, pk=subsistema_id, activo=True)
    variables = Variable.objects.filter(subsistema=subsistema, activo=True)
    tema = subsistema.sistema.tema
    return render(request, 'haapar_unla_app/variable-detalle.html', {
        "subsistema": subsistema,
        "variables": variables,
        "tema": tema,
    })


@login_required
def crear_variable(request, subsistema_id):
    subsistema = get_object_or_404(Subsistema, pk=subsistema_id, activo=True)
    
    # Captura el origen cuando entramos a la página (GET)
    next_view = request.GET.get('next', '')

    if request.method == "POST":
        variable = Variable.objects.create(
            nombre=request.POST.get("nombre"),
            nombre_corto=request.POST.get("nombre_corto"),
            descripcion=request.POST.get("descripcion"),
            tipo=request.POST.get("tipo"),
            subsistema=subsistema
        )
        Historial.objects.create(
            variable=variable,
            usuario=request.user,
            accion='AGREGADO'
        )
        
        # Lee el origen cuando mandamos el formulario (POST)
        next_post = request.POST.get('next', '')
        
        if next_post == 'matriz':
            # REDIRECCIÓN CORREGIDA CON GUION MEDIO
            return redirect("editar-matriz", subsistema_id=subsistema_id)
            
        return redirect("variable_detalle", subsistema_id=subsistema_id)

    return render(request, "haapar_unla_app/crear-variable.html", {
        "subsistema": subsistema,
        "next": next_view
    })


@login_required
def editar_variable(request, pk):
    variable = get_object_or_404(Variable, pk=pk, activo=True)
    subsistema_id = variable.subsistema.id_subsistema
    
    # Leemos el parámetro oculto
    next_view = request.GET.get('next', '')

    if request.method == "POST":
        # 1. Guardamos cómo se llamaba ANTES de pisar los datos
        old_nombre = variable.nombre
        old_nombre_corto = variable.nombre_corto

        # 2. Obtenemos los datos NUEVOS del formulario
        new_nombre = request.POST.get("nombre")
        new_nombre_corto = request.POST.get("nombre_corto")

        # 3. Actualizamos la variable
        variable.nombre = new_nombre
        variable.nombre_corto = new_nombre_corto
        variable.descripcion = request.POST.get("descripcion")
        variable.tipo = request.POST.get("tipo")
        variable.save()

        # 4. Armamos el texto para la columna "Detalles"
        cambios = []
        if old_nombre != new_nombre:
            cambios.append(f"Nombre: '{old_nombre}' ➔ '{new_nombre}'")
        if old_nombre_corto != new_nombre_corto:
            cambios.append(f"Corto: '{old_nombre_corto}' ➔ '{new_nombre_corto}'")
        
        # Si cambiaron los nombres, los unimos. Si no, ponemos un mensaje genérico.
        texto_detalle = " | ".join(cambios) if cambios else "Modificación de descripción/tipo"

        # 5. Guardamos en el historial CON el detalle
        Historial.objects.create(
            variable=variable,
            usuario=request.user,
            accion='MODIFICADO',
            detalles=texto_detalle
        )
        
        # Redirección
        next_post = request.POST.get('next', '')
        if next_post == 'matriz':
            return redirect("editar-matriz", subsistema_id=subsistema_id)
            
        return redirect("variable_detalle", subsistema_id=subsistema_id)

    return render(request, "haapar_unla_app/editar-variable.html", {
        "variable": variable,
        "subsistema_id": subsistema_id,
        "next": next_view
    })


@login_required
@require_POST
def eliminar_variable(request, pk):
    variable = get_object_or_404(Variable, pk=pk, activo=True)
    subsistema_id = variable.subsistema.id_subsistema
    
    # Leemos de dónde viene el clic
    next_view = request.GET.get('next', '')

    variable.activo = False
    variable.save()

    Historial.objects.create(
        variable=variable,
        usuario=request.user,
        accion='ELIMINADO'
    )
    
    # Decidimos a dónde redireccionar
    if next_view == 'matriz':
        return redirect("editar-matriz", subsistema_id=subsistema_id)
        
    return redirect("variable_detalle", subsistema_id=subsistema_id)


@login_required
def historial_variables(request, subsistema_id):
    historial = Historial.objects.select_related(
        'variable', 'usuario'
    ).filter(
        variable__subsistema_id=subsistema_id
    ).order_by('-fecha')

    # Capturamos de dónde viene el usuario
    from_view = request.GET.get('from', '')

    return render(request, "haapar_unla_app/historial-variable.html", {
        "historial": historial,
        "subsistema_id": subsistema_id,
        "from_view": from_view  # Se lo pasamos al HTML
    })


# ---------------------------
# SUBSISTEMAS
# ---------------------------
@login_required
def subsistemas(request, tema_id):
    tema = get_object_or_404(Tema, id_tema=tema_id, activo=True)

    # Verificar permisos: creador o colaborador
    if request.user != tema.user and request.user not in tema.colaboradores.all():
        return HttpResponseForbidden("No tenés permiso para ver este proyecto.")

    sistemas = Sistema.objects.filter(tema=tema).prefetch_related(
        Prefetch('subsistema_set', queryset=Subsistema.objects.filter(activo=True))
    )
    return render(request, 'haapar_unla_app/subsistemas.html', {
        'tema': tema,
        'sistemas': sistemas
    })


@login_required
def crear_subsistema(request, tema_id):
    tema = get_object_or_404(Tema, pk=tema_id)
    sistema, _ = Sistema.objects.get_or_create(
        tema=tema,
        defaults={
            "nombre": f"Sistema de {tema.nombre}",
            "descripcion": "Sistema generado automáticamente"
        }
    )
    if request.method == "POST":
        Subsistema.objects.create(
            sistema=sistema,
            nombre=request.POST.get("nombre"),
            descripcion=request.POST.get("descripcion"),
            activo=True
        )
        return redirect("subsistemas", tema_id=tema.id_tema)
    return render(request, "haapar_unla_app/crear-subsistema.html", {"tema": tema})


@login_required
def eliminar_subsistema(request, sub_id):
    sub = get_object_or_404(Subsistema, id_subsistema=sub_id, sistema__tema__user=request.user)
    if request.method == 'POST':
        sub.activo = False
        sub.save()
    return redirect('subsistemas', tema_id=sub.sistema.tema.id_tema)


# ---------------------------
# AUTENTICACIÓN
# ---------------------------
def registro(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()

        existing = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=email)).first()
        if existing and not existing.is_active:
            current_site = get_current_site(request)
            uid = urlsafe_base64_encode(force_bytes(existing.pk))
            token = default_token_generator.make_token(existing)
            reactivate_link = request.build_absolute_uri(reverse('reactivar_cuenta', kwargs={'uidb64': uid, 'token': token}))
            subject = 'Reactivar tu cuenta'
            message = render_to_string('haapar_unla_app/autenticacion/reactivar_cuenta_email.txt', {
                'user': existing,
                'reactivate_link': reactivate_link,
                'domain': current_site.domain,
            })
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [existing.email], fail_silently=False)
                messages.info(request, 'Hemos enviado un email para reactivar tu cuenta. Revisa tu bandeja de entrada.')
            except BadHeaderError:
                messages.error(request, 'Error al enviar el email de reactivación.')
            form = SignUpForm()
            return render(request, 'haapar_unla_app/autenticacion/signup.html', {'form': form})

        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("inicio")
    else:
        form = SignUpForm()
    return render(request, 'haapar_unla_app/autenticacion/signup.html', {'form': form})

def reactivar_cuenta(request, uidb64, token):
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
                user.first_name = request.POST.get('first_name', user.first_name)
                user.last_name = request.POST.get('last_name', user.last_name)
                user.is_active = True
                user.save()
                login(request, user)
                messages.success(request, 'Cuenta reactivada correctamente.')
                return redirect('inicio')
        else:
            form = SetPasswordForm(user)
        return render(request, 'haapar_unla_app/autenticacion/reactivar_cuenta.html', {
            'form': form,
            'reactivate_user': user
        })
    else:
        messages.error(request, 'El enlace de reactivación no es válido o ha expirado.')
        return redirect('registro')

def cerrar_sesion(request):
    logout(request)
    return redirect("inicio")


def iniciar_sesion(request):
    if request.method == 'GET':
        return render(request, "haapar_unla_app/autenticacion/signin.html", {'form': AuthenticationForm()})
    else:
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, "haapar_unla_app/autenticacion/signin.html", {
                'form': AuthenticationForm(),
                'error': 'El usuario o la contraseña son incorrectas.'
            })
        login(request, user)
        return redirect('inicio')


# ---------------------------
# PERFIL
# ---------------------------
@login_required
def perfil(request):
    user = request.user

    form = ProfileForm(instance=user)
    pass_form = PasswordChangeForm(user)

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
            else:
                messages.error(request, 'No se pudo cambiar la contraseña. Revisa los errores del formulario.')

        elif 'delete_profile' in request.POST:
            user.is_active = False
            user.save()
            messages.error(request, "Tu cuenta fue desactivada correctamente.")
            logout(request)
            return redirect("inicio")

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
@login_required 
def actor_detalle(request, subsistema_id):
    subsistema = get_object_or_404(Subsistema, id_subsistema=subsistema_id)
    actores = ActorClave.objects.filter(subsistema=subsistema, activo=True)
    tema = subsistema.sistema.tema
    return render(request, 'haapar_unla_app/actor-detalle.html', {
        'subsistema': subsistema,
        'actores': actores,
        'tema': tema
    })

@login_required
def crear_actor(request, subsistema_id):
    subsistema = get_object_or_404(Subsistema, id_subsistema=subsistema_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        puesto = request.POST.get('puesto')
        actor = ActorClave.objects.create(
            subsistema=subsistema,
            nombre=nombre,
            descripcion=descripcion,
            puesto=puesto,
            activo=True
        )
        
        influencia = request.POST.get('influencia')
        if influencia:
            RelacionActor.objects.create(
                actor_clave=actor,
                subsistema=subsistema,
                influencia=influencia
            )
        return redirect('actor_detalle', subsistema_id=subsistema.id_subsistema)

    return render(request, 'haapar_unla_app/crear-actor.html', {
        'subsistema': subsistema
    })

@login_required
def editar_actor(request, pk):
    actor = get_object_or_404(ActorClave, pk=pk)
    subsistema = actor.subsistema

    if request.method == 'POST':
        actor.nombre = request.POST.get('nombre', actor.nombre)
        actor.descripcion = request.POST.get('descripcion', actor.descripcion)
        actor.puesto = request.POST.get('puesto', actor.puesto)
        actor.save()
        
        influencia = request.POST.get('influencia')
        if influencia:
            relacion, created = RelacionActor.objects.get_or_create(
                actor_clave=actor,
                subsistema=subsistema,
                defaults={'influencia': influencia}
            )
            if not created:
                relacion.influencia = influencia
                relacion.save()

        return redirect('actor_detalle', subsistema_id=subsistema.id_subsistema)

    try:
        relacion = RelacionActor.objects.get(actor_clave=actor, subsistema=subsistema)
        influencia = relacion.influencia
    except RelacionActor.DoesNotExist:
        influencia = None

    return render(request, 'haapar_unla_app/editar-actor.html', {
        'actor': actor,
        'influencia': influencia,
        'subsistema': subsistema
    })

@login_required
@require_POST
def eliminar_actor(request, pk):
    actor = get_object_or_404(ActorClave, pk=pk)
    actor.activo = False
    actor.save()
    return redirect('actor_detalle', subsistema_id=actor.subsistema.id_subsistema)


# ---------------------------
# TENDENCIAS
# ---------------------------
@login_required
def listar_tendencias(request):
    tendencias_por_subsistema = Subsistema.objects.annotate(
        num_tendencias=Count('tendenciaexterna', filter=Q(tendenciaexterna__activo=True), distinct=True)
    ).filter(num_tendencias__gt=0)
    todas_las_tendencias = TendenciaExterna.objects.filter(activo=True)
    return render(request, 'haapar_unla_app/tendencias.html', {
        'tendencias_por_subsistema': tendencias_por_subsistema,
        'todas_las_tendencias': todas_las_tendencias,
    })

@login_required
def tendencia_detalle(request, tema_id=None, subsistema_id=None):
    if tema_id:
        tema = get_object_or_404(Tema, id_tema=tema_id)
        tendencias = TendenciaExterna.objects.filter(tema=tema, activo=True)
        return render(request, 'haapar_unla_app/tendencia-detalle.html', {
            'tema': tema,
            'tendencias': tendencias
        })
    elif subsistema_id:
        subsistema = get_object_or_404(Subsistema, id_subsistema=subsistema_id, activo=True)
        tema = subsistema.sistema.tema
        tendencias = TendenciaExterna.objects.filter(subsistema=subsistema, activo=True)
        return render(request, 'haapar_unla_app/tendencia-detalle.html', {
            'tema': tema,
            'subsistema': subsistema,
            'tendencias': tendencias,
        })

@login_required
def crear_tendencia(request, subsistema_id):
    subsistema = get_object_or_404(Subsistema, id_subsistema=subsistema_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        nombre_corto = request.POST.get('nombre_corto')
        tipo_dato = request.POST.get('tipo_dato')
        descripcion = request.POST.get('descripcion')

        TendenciaExterna.objects.create(
            subsistema=subsistema,
            nombre=nombre,
            nombre_corto=nombre_corto,
            tipo_dato=tipo_dato,
            descripcion=descripcion,
            activo=True
        )

        return redirect('tendencia_detalle', subsistema_id=subsistema.id_subsistema)

    return render(request, 'haapar_unla_app/crear-tendencia.html', {
        'subsistema': subsistema,
    })

@login_required
def editar_tendencia(request, pk):
    tendencia = get_object_or_404(TendenciaExterna, pk=pk, activo=True)
    subsistema = tendencia.subsistema

    if request.method == 'POST':
        tendencia.nombre = request.POST.get('nombre', tendencia.nombre)
        tendencia.nombre_corto = request.POST.get('nombre_corto', tendencia.nombre_corto)
        tendencia.tipo_dato = request.POST.get('tipo_dato', tendencia.tipo_dato)
        tendencia.descripcion = request.POST.get('descripcion', tendencia.descripcion)
        tendencia.save()

        return redirect('tendencia_detalle', subsistema_id=subsistema.id_subsistema)

    return render(request, 'haapar_unla_app/editar-tendencia.html', {
        'tendencia': tendencia,
        'subsistema': subsistema,
    })

@login_required
def eliminar_tendencia(request, pk):
    tendencia = get_object_or_404(TendenciaExterna, pk=pk, activo=True)
    subsistema_id = tendencia.subsistema.id_subsistema
    if request.method == 'POST':
        tendencia.activo = False
        tendencia.save()
    return redirect('tendencia_detalle', subsistema_id=subsistema_id)


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

# ---------------------------
# ChatGPT API wrapper (simple)
# ---------------------------
# @csrf_exempt
# @require_POST
# def chatgpt_api(request):
    """Endpoint simple que recibe JSON {"prompt": "..."} y retorna la respuesta de ChatGPT en JSON."""
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'success': False, 'error': 'JSON inválido en cuerpo'}, status=400)

    prompt = payload.get('prompt')
    if not prompt:
        return JsonResponse({'success': False, 'error': 'Falta campo "prompt"'}, status=400)

    result = generate_chat_completion(prompt)
    if not result.get('success'):
        return JsonResponse({'success': False, 'error': result.get('error')}, status=500)

    return JsonResponse({'success': True, 'text': result.get('text')})
#

# ---------------------------------------------------------
# VISTA PRINCIPAL (FODA Y GRÁFICOS)
# ---------------------------------------------------------
@login_required
def foda_graficos(request, subsistema_id):
    subsistema = get_object_or_404(Subsistema, pk=subsistema_id, activo=True)
    tema = subsistema.sistema.tema

    if request.user != tema.user and request.user not in tema.colaboradores.all():
        return HttpResponseForbidden("No tenés permiso para ver este proyecto.")

    # ACÁ SE FILTRA POR SUBSISTEMA PARA QUE NO SE REPITAN LAS VARIABLES
    variables_obj = Variable.objects.filter(
        subsistema=subsistema,
        activo=True
    ).prefetch_related('pestels').order_by('pk')

    nombres_vars = [v.nombre_corto if v.nombre_corto else v.nombre[:15] for v in variables_obj]

    importancias = [int(v.promedio_importancia()) for v in variables_obj]
    incertidumbres = [int(v.promedio_incertidumbre()) for v in variables_obj]

    datos_dispersion = {
        "variables": nombres_vars,
        "importancia": importancias,
        "incertidumbre": incertidumbres
    }

    n = len(variables_obj)
    matriz_valores = [[0] * n for _ in range(n)]
    var_index = {v.pk: i for i, v in enumerate(variables_obj)}

    influencias = Influencia.objects.filter(
        variable_origen__in=variables_obj,
        variable_destino__in=variables_obj
    )

    for inf in influencias:
        i = var_index[inf.variable_origen.pk] 
        j = var_index[inf.variable_destino.pk] 
        matriz_valores[i][j] = int(inf.valor)

    matriz_indirecta = {
        "variables": nombres_vars,
        "valores": matriz_valores
    }

    influencia_totales = [sum(fila) for fila in matriz_valores]
    dependencia_totales = [sum(matriz_valores[i][j] for i in range(n)) for j in range(n)]

    datos_micmac = {
        "variables": nombres_vars,
        "influencia": influencia_totales,
        "dependencia": dependencia_totales
    }

    datos_pestel = {}
    
    for var in variables_obj:
        nombre_var = var.nombre_corto or var.nombre[:15]
        for pestel in var.pestels.all():
            categoria = pestel.get_tipo_display() 
            if categoria not in datos_pestel:
                datos_pestel[categoria] = []
            datos_pestel[categoria].append(nombre_var)

    contexto = {
        'tema': tema,
        'subsistema': subsistema,
        'datos_dispersion': json.dumps(datos_dispersion),
        'variables': nombres_vars,
        'filas': zip(nombres_vars, matriz_valores),
        'matriz_indirecta': json.dumps(matriz_indirecta),
        'datos_micmac': json.dumps(datos_micmac),
        'datos_pestel': json.dumps(datos_pestel),
    }

    return render(request, "haapar_unla_app/foda-graficos.html", contexto)

@login_required
def asignar_colaboradores(request, tema_id):
    tema = get_object_or_404(Tema, pk=tema_id)
    es_creador = (request.user == tema.user)

    if request.method == "POST" and es_creador:
        colaboradores_ids = request.POST.getlist("colaboradores")
        colaboradores = User.objects.filter(id__in=colaboradores_ids)
        tema.colaboradores.set(colaboradores)

        # ✅ Cambio aquí: usar get_or_create en vez de get
        grupo_colaborador, _ = Group.objects.get_or_create(name="colaborador")
        for u in colaboradores:
            u.groups.add(grupo_colaborador)

        return redirect("listar_proyectos")

    return render(request, "haapar_unla_app/asignar_colaboradores.html", {
        "tema": tema,
        "usuarios": User.objects.exclude(id=tema.user.id),
        "es_creador": es_creador
    })

    


def about(request):
    return render(request, 'haapar_unla_app/about.html')


def blog_details(request):
    return render(request, 'haapar_unla_app/blog-details.html')


def blog(request):  # Esta es la vista que faltaba
    return render(request, 'haapar_unla_app/blog.html')


def contact(request):
    return render(request, 'haapar_unla_app/contact.html')


def portfolio_details(request):
    return render(request, 'haapar_unla_app/portfolio-details.html')


def portfolio(request):
    return render(request, 'haapar_unla_app/portfolio.html')


def service_details(request):
    return render(request, 'haapar_unla_app/service-details.html')


def services(request):
    return render(request, 'haapar_unla_app/services.html')


def starter_page(request):
    return render(request, 'haapar_unla_app/starter-page.html')


def team(request):
    return render(request, 'haapar_unla_app/team.html')


# Vista para manejar el error 400
def error_400_view(request, exception):
    return render(request, 'haapar_unla_app/error/400.html', status=400)


# Vista para manejar el error 403
def error_403_view(request, exception):
    return render(request, 'haapar_unla_app/error/403.html', status=403)


# Vista para manejar el error 404
def error_404_view(request, exception):
    return render(request, 'haapar_unla_app/error/404.html', status=404)


# Vista para manejar el error 500
def error_500_view(request):
    return render(request, 'haapar_unla_app/error/500.html', status=500)

# ---------------------------------------------------------
# ABM MANUAL DE LA MATRIZ MATEMÁTICA
# ---------------------------------------------------------
@login_required
def editar_matriz(request, subsistema_id):
    subsistema = get_object_or_404(Subsistema, pk=subsistema_id, activo=True)
    tema = subsistema.sistema.tema

    if request.user != tema.user and request.user not in tema.colaboradores.all():
        return HttpResponseForbidden("No tenés permiso para editar este proyecto.")

    variables = list(Variable.objects.filter(subsistema=subsistema, activo=True).order_by('pk'))

    if request.method == 'POST':
        #ALTA/MODIFICACIÓN DE EVALUACIONES MANUALES ---
        for var in variables:
            imp_val = request.POST.get(f'imp_{var.pk}')
            inc_val = request.POST.get(f'inc_{var.pk}')
            
            if imp_val and inc_val:
                imp_val = int(imp_val)
                inc_val = int(inc_val)
                
                eval_obj = EvaluacionVariable.objects.filter(variable=var, usuario=request.user).first()
                old_imp = eval_obj.importancia if eval_obj else "Vacío"
                old_inc = eval_obj.incertidumbre if eval_obj else "Vacío"

                if not eval_obj or old_imp != imp_val or old_inc != inc_val:
                    # Esto hace el ALTA si no existe, o MODIFICA si ya existe
                    EvaluacionVariable.objects.update_or_create(
                        variable=var,
                        usuario=request.user,
                        defaults={'importancia': imp_val, 'incertidumbre': inc_val}
                    )
                    
                    texto_detalle = f"Imp: {old_imp} ➔ {imp_val} | Inc: {old_inc} ➔ {inc_val}"
                    Historial.objects.create(variable=var, usuario=request.user, accion='EVALUACION', detalles=texto_detalle)

        # ALTA/MODIFICACIÓN DE INFLUENCIAS ---
        for origen in variables:
            for destino in variables:
                if origen.pk != destino.pk:
                    inf_val = request.POST.get(f'inf_{origen.pk}_{destino.pk}')
                    if inf_val is not None:
                        inf_val = float(inf_val)
                        inf_obj = Influencia.objects.filter(variable_origen=origen, variable_destino=destino).first()
                        old_inf = float(inf_obj.valor) if inf_obj else "Vacío"
                        
                        if not inf_obj or old_inf != inf_val:
                            # Esto hace el ALTA si no existe, o MODIFICA si ya existe
                            Influencia.objects.update_or_create(
                                variable_origen=origen,
                                variable_destino=destino,
                                defaults={'valor': inf_val}
                            )
                            texto_detalle = f"Influencia sobre '{destino.nombre_corto}': {old_inf} ➔ {int(inf_val)}"
                            Historial.objects.create(variable=origen, usuario=request.user, accion='MODIFICADO', detalles=texto_detalle)
        
        messages.success(request, '¡Valores actualizados! Los gráficos se recalcularon.')
        return redirect('foda_graficos', subsistema_id=subsistema.id_subsistema)

    # --- ACÁ SE PREPARA LA VISTA Y SE CALCULAN LOS PROMEDIOS ---
    filas_tabla = []
    for origen in variables:
        eval_obj = EvaluacionVariable.objects.filter(variable=origen, usuario=request.user).first()
        
        # ACÁ SE APLICA EL PROMEDIO: Si el usuario no votó, trae el promedio (IA + otros usuarios)
        try: imp_clean = max(1, min(10, int(round(float(eval_obj.importancia if eval_obj else (origen.promedio_importancia() or 1))))))
        except: imp_clean = 1
        
        try: inc_clean = max(1, min(10, int(round(float(eval_obj.incertidumbre if eval_obj else (origen.promedio_incertidumbre() or 1))))))
        except: inc_clean = 1

        celdas = []
        for destino in variables:
            if origen.pk == destino.pk:
                celdas.append({'destino_id': destino.pk, 'valor': '-', 'is_self': True})
            else:
                inf_obj = Influencia.objects.filter(variable_origen=origen, variable_destino=destino).first()
                try: inf_clean = max(0, min(3, int(round(float(inf_obj.valor if inf_obj else 0)))))
                except: inf_clean = 0
                celdas.append({'destino_id': destino.pk, 'valor': inf_clean, 'is_self': False})

        filas_tabla.append({'origen': origen, 'imp': imp_clean, 'inc': inc_clean, 'celdas': celdas})

    return render(request, 'haapar_unla_app/editar-matriz.html', {
        'tema': tema,
        'subsistema': subsistema,
        'variables': variables,
        'filas_tabla': filas_tabla
    })
    
    # ==========================================
# ENDPOINT DE IA UNIFICADO
# ==========================================
@login_required
@require_POST
def chatgpt_api(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'success': False, 'error': 'JSON inválido en cuerpo'}, status=400)

    prompt = payload.get('prompt')
    if not prompt:
        return JsonResponse({'success': False, 'error': 'Falta campo "prompt"'}, status=400)

    # Usamos el cliente unificado nuevo
    result = generar_respuesta_llm(prompt)
    
    if not result.get('success'):
        return JsonResponse({'success': False, 'error': result.get('error')}, status=500)

    return JsonResponse({'success': True, 'text': result.get('text')})
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
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from django.template.loader import render_to_string
from django.core.mail import send_mail, BadHeaderError
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse
from django.db.models import Prefetch, Count, Q

from .forms import SignUpForm
from haapar_unla_app.models import (
    Tema, Sistema, Subsistema, Variable,
    Evaluacion, TendenciaExterna,ActorClave,RelacionActor
)
from django.shortcuts import render
import json
import datetime
# Cliente OpenAI (ChatGPT)
 

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
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        horizonte = request.POST.get('horizonte')
        territorio = request.POST.get('territorio')

        tema = Tema.objects.create(
            user=request.user,
            nombre=nombre,
            descripcion=descripcion,
            horizonte=horizonte,
            territorio=territorio
        )
        request.session['reporte_tema'] = tema.id_tema
        return redirect('subsistemas', tema_id=tema.id_tema)

    return render(request, 'haapar_unla_app/crear-reporte.html')


@login_required
def listar_proyectos(request):
    temas = Tema.objects.filter(user=request.user, activo=True)
    return render(request, 'haapar_unla_app/listar-proyectos.html', {'temas': temas})


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

    if request.method == "POST":
        variable = Variable.objects.create(
            nombre=request.POST.get("nombre"),
            nombre_corto=request.POST.get("nombre_corto"),
            descripcion=request.POST.get("descripcion"),
            tipo=request.POST.get("tipo"),
            subsistema=subsistema
        )
        Evaluacion.objects.create(
            variable=variable,
            importancia=0,
            incertidumbre=0,
            usuario_creador=request.user,
            usuario_modificador=request.user,
            accion='CREADO'
        )
        return redirect("variable_detalle", subsistema_id=subsistema.id_subsistema)

    return render(request, "haapar_unla_app/crear-variable.html", {"subsistema": subsistema})


@login_required
def editar_variable(request, pk):
    variable = get_object_or_404(Variable, pk=pk, activo=True)
    subsistema_id = variable.subsistema.id_subsistema

    if request.method == "POST":
        variable.nombre = request.POST.get("nombre")
        variable.nombre_corto = request.POST.get("nombre_corto")
        variable.descripcion = request.POST.get("descripcion")
        variable.tipo = request.POST.get("tipo")
        variable.save()

        Evaluacion.objects.create(
            variable=variable,
            importancia=0,
            incertidumbre=0,
            usuario_creador=request.user,
            usuario_modificador=request.user,
            accion='MODIFICADO'
        )
        return redirect("variable_detalle", subsistema_id=subsistema_id)

    return render(request, "haapar_unla_app/editar-variable.html", {
        "variable": variable,
        "subsistema_id": subsistema_id
    })


@login_required
def eliminar_variable(request, pk):
    variable = get_object_or_404(Variable, pk=pk, activo=True)
    subsistema_id = variable.subsistema.id_subsistema

    variable.activo = False
    variable.save()

    Evaluacion.objects.create(
        variable=variable,
        importancia=0,
        incertidumbre=0,
        usuario_creador=request.user,
        usuario_modificador=request.user,
        accion='ELIMINADO'
    )
    return redirect("variable_detalle", subsistema_id=subsistema_id)


@login_required
def historial_variables(request, subsistema_id):
    historial = Evaluacion.objects.select_related(
        'variable', 'usuario_creador'
    ).filter(
        variable__subsistema_id=subsistema_id
    ).order_by('-fecha_modificacion')

    return render(request, "haapar_unla_app/historial-variable.html", {
        "historial": historial,
        "subsistema_id": subsistema_id
    })


# ---------------------------
# SUBSISTEMAS
# ---------------------------
@login_required
def subsistemas(request, tema_id):
    tema = get_object_or_404(Tema, id_tema=tema_id, user=request.user)
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
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("inicio")
    else:
        form = SignUpForm()
    return render(request, 'haapar_unla_app/autenticacion/signup.html', {'form': form})


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
        # Actualizar o crear la relación de influencia
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
def tendencia_detalle(request, tema_id):
    tema = get_object_or_404(Tema, id_tema=tema_id)
    tendencias = TendenciaExterna.objects.filter(tema=tema, activo=True)
    return render(request, 'haapar_unla_app/tendencia-detalle.html', {
        'tema': tema,
        'tendencias': tendencias
    })


@login_required
def tendencia_detalle(request, subsistema_id):
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
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .infraestructura.api_client.openai_client import generate_chat_completion
@csrf_exempt
@require_POST
def chatgpt_api(request):
    """Endpoint simple que recibe JSON {"prompt": "..."} y retorna la respuesta de ChatGPT en JSON.

    Nota: protege este endpoint en producción (auth, rate limit, logging).
    """
    try:
        import json
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

#Creacion de graficos para el analisis FODA
def foda_graficos(request):
    datos_dispersion = {
        "variables": ["Var1", "Var2", "Var3"],
        "importancia": [5, 3, 7],
        "incertidumbre": [2, 6, 4],
    }

    variables = [
        "cant_de_min_de_jueg",
        "nmer_de_gale_antl_po",
        "tasa_de_lesi_por_tem",
        "nive_de_comp_en_liJ",
        "grad_de_desa_fisc_y"
    ]
    matriz = [
        [0, 2, 2, 1, 3],
        [1, 0, 1, 0, 2],
        [3, 1, 0, 2, 3],
        [2, 2, 2, 0, 3],
        [1, 2, 2, 2, 0],
    ]
    filas = list(zip(variables, matriz))

    # Datos para el eje Peter-Schwartz
    peter_schwartz = {
        "x_label": "Proyecciones de rendimiento de expertos",
        "y_label": "Habilidades técnicas actuales",
        "cuadrantes": [
            {"nombre": "Estrella Ascendente", "pos": (1, 1)},
            {"nombre": "Experto en Evolución", "pos": (-1, 1)},
            {"nombre": "Retroceso Competitivo", "pos": (-1, -1)},
            {"nombre": "Proyección Brillante", "pos": (1, -1)},
        ]
    }

    return render(request, "haapar_unla_app/foda-graficos.html", {
        "datos_dispersion": datos_dispersion,
        "variables": variables,
        "filas": filas,
        "peter_schwartz": peter_schwartz
    })

# Variables y matriz de relaciones indirectas para el análisis MICMAC

def micmac_indirecto(request):
    variables = [
        "cant_de_mime_de_jueg",
        "mime_de_jueg_ant_pos",
        "tasa_de_jueg_ben",
        "nive_de_comp_eju_i",
        "grad_de_desa_fisc_x"
    ]
    matriz_indirecta = [
        [0, 2, 1, 3, 2],
        [1, 0, 2, 2, 1],
        [2, 1, 0, 3, 2],
        [1, 2, 2, 0, 3],
        [2, 1, 2, 2, 0],
    ]
    filas = list(zip(variables, matriz_indirecta))

    influencia = [sum(fila) for fila in matriz_indirecta]
    dependencia = [sum(col) for col in zip(*matriz_indirecta)]

    datos_micmac = {
        "variables": variables,
        "influencia": influencia,
        "dependencia": dependencia,
    }

    return render(request, "haapar_unla_app/foda-graficos.html", {
        "variables": variables,
        "filas": filas,
        "datos_micmac": json.dumps(datos_micmac)  # 👈 JSON válido
    })

#Grafico de dispersion para el analisis MICMAC 

def micmac_dispersion(request):
    variables = [
        "niv_de_comp_un_Lic",
        "tasa_de_jueg_ben",
        "grad_de_desa_fisc_x",
        "mime_de_jueg_ant_pos",
        "cant_de_mime_de_jueg"
    ]

    # Ejemplo de matriz (puedes reemplazar con la tuya)
    matriz = [
        [0, 2, 1, 3, 2],
        [1, 0, 2, 2, 1],
        [2, 1, 0, 3, 2],
        [1, 2, 2, 0, 3],
        [2, 1, 2, 2, 0],
    ]

    # Cálculo de influencia y dependencia
    influencia = [sum(fila) for fila in matriz]
    dependencia = [sum(col) for col in zip(*matriz)]

    datos_dispersion = {
        "variables": variables,
        "influencia": influencia,
        "dependencia": dependencia,
    }

    return render(request, "haapar_unla_app/foda-graficos.html", {
        "variables": variables,
        "matriz": matriz,
        "datos_dispersion": json.dumps(datos_dispersion)
    })
    

def pestel_arbol(request):
    print("Entrando a la vista pestel_arbol")  #PRUEBO SI SALE EN CONSOLA
    pestel_data = {
        "Político": [
            "Políticas públicas tecnológicas",
            "Estabilidad gubernamental"
        ],
        "Económico": [
            "Inflación",
            "Costo de infraestructura",
            "Financiamiento"
        ],
        "Social": [
            "Adopción tecnológica",
            "Capacitación de usuarios"
        ],
        "Tecnológico": [
            "Innovación en software",
            "Ciberseguridad"
        ],
        "Ecológico": [
            "Consumo energético",
            "Sustentabilidad"
        ],
        "Legal": [
            "Protección de datos",
            "Regulaciones IT"
        ]
    }
    # CONSOLE LOG EN EL SERVIDOR
    pestel_json = json.dumps(pestel_data, ensure_ascii=False)
    print("=" * 50)
    print("DATOS PESTEL ENVIADOS AL TEMPLATE:")
    print("=" * 50)
    print(pestel_json)
    print("=" * 50)
    print(f"Tipo de dato: {type(pestel_json)}")
    print("=" * 50)

    return render(request, "foda-graficos.html", {
        "pestel": json.dumps(pestel_data, ensure_ascii=False)  
    })


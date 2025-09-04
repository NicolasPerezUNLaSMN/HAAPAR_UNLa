from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required

from .forms import SignUpForm, TemaForm
from django.contrib.auth import get_user_model


from haapar_unla_app.aplicaciones.casos_uso.registrar_usuario import RegistrarUsuario
from haapar_unla_app.aplicaciones.casos_uso.iniciar_sesion import IniciarSesion
from haapar_unla_app.aplicaciones.casos_uso.cerrar_sesion import CerrarSesion
from haapar_unla_app.infraestructura.persistencia.usuario_repositorio_db import UsuarioRepositorioDB
from django.contrib.auth import authenticate


from haapar_unla_app.aplicaciones.casos_uso.crear_tema import CrearTema
from haapar_unla_app.infraestructura.persistencia.tema_repositorio_db import TemaRepositorioDB



def inicio(request):
    return render(request, 'haapar_unla_app/crear-reporte.html')


def listar_proyectos(request):
    return render(request, 'haapar_unla_app/listar-proyectos.html')


def proyecto_detalle(request):
    return render(request, 'haapar_unla_app/proyecto-detalle.html')


def variable_detalle(request):
    return render(request, 'haapar_unla_app/variable-detalle.html')

"""
def crear_reporte(request):
    if request.method == 'POST':
        # Procesar los datos del formulario
        tema = request.POST.get('tema')
        anio = request.POST.get('anio')
        grado = request.POST.get('grado')
        
        # Guardar los datos en la sesión para usarlos en la siguiente vista
        request.session['reporte_tema'] = tema
        request.session['reporte_anio'] = anio
        request.session['reporte_grado'] = grado
        
        # Redirigir a la vista de subsistemas
        return redirect('subsistemas')
    
    # Si es GET, mostrar el formulario vacío
    return render(request, 'haapar_unla_app/crear-reporte.html')"""

def subsistemas(request):
    if request.method == 'GET':
        # Recuperar parámetros de la URL
        tema = request.GET.get('tema', request.session.get('reporte_tema', 'TEMA NO ESPECIFICADO'))
        anio = request.GET.get('anio', request.session.get('reporte_anio', ''))
        grado = request.GET.get('grado', request.session.get('reporte_grado', ''))
        
        # Guardar en sesión por si acaso
        request.session['reporte_tema'] = tema
        request.session['reporte_anio'] = anio
        request.session['reporte_grado'] = grado
    
    return render(request, 'haapar_unla_app/subsistemas.html', {
        'tema': tema,
        'anio': anio,
        'grado': grado
    })


def registro(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                repositorio = UsuarioRepositorioDB()
                caso_uso = RegistrarUsuario(repositorio)
                
                usuario_creado = caso_uso.ejecutar(
                    username=form.cleaned_data['username'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    grupo_id=1
                )
                
                user = authenticate(
                    request,
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password']
                )
                if user:
                    login(request, user)
                
                return redirect('inicio')
                
            except ValueError as e:
                form.add_error(None, str(e))          
    
    else:  
        form = SignUpForm()
    
    
    return render(request, 'haapar_unla_app/autenticacion/signup.html', {'form': form})

def cerrar_sesion(request):
    try:
        repositorio = UsuarioRepositorioDB()
        caso_uso = CerrarSesion(repositorio)
        
        # Ejecutar caso de uso
        caso_uso.ejecutar(request)
        
        # Redirigir a la página de inicio
        return redirect('inicio')
        
    except Exception as e:
        # En caso de error, igual redirigir pero podrías loggear el error
        print(f"Error al cerrar sesión: {e}")
        return redirect('inicio')


def iniciar_sesion(request):
    if request.method == 'GET':
        return render(request, "haapar_unla_app/autenticacion/signin.html", {
            'form': AuthenticationForm()
        })
    
    else:  
        try:
            form = AuthenticationForm(request, data=request.POST)
            
            if form.is_valid():        
                repositorio = UsuarioRepositorioDB()
                caso_uso = IniciarSesion(repositorio)
                
                usuario_entidad = caso_uso.ejecutar(
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password']
                )
                          
                # Obtener el modelo de Django para hacer login
                User = get_user_model()
                user_model = User.objects.get(username=usuario_entidad.username)
                
                login(request, user_model)
                              
                return redirect('inicio')
                
            else:
                return render(request, "haapar_unla_app/autenticacion/signin.html", {
                    'form': form,
                    'error': 'Por favor corrige los errores del formulario'
                })
                
        except ValueError as e:
            return render(request, "haapar_unla_app/autenticacion/signin.html", {
                'form': form,
                'error': str(e)
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            return render(request, "haapar_unla_app/autenticacion/signin.html", {
                'form': form,
                'error': f'Error inesperado: {str(e)}'
            })


#------------- Tema -------------------------------
@login_required
def crear_tema(request):
    if request.method == 'POST':
        form = TemaForm(request.POST)
        if form.is_valid():
            repositorio = TemaRepositorioDB()
            caso_uso = CrearTema(repositorio)
            
            # Más claro con nombre específico
            tema_creado = caso_uso.crear(
                user_id=request.user.id,
                nombre=form.cleaned_data['nombre'],
                descripcion=form.cleaned_data['descripcion'],
                horizonte=form.cleaned_data['horizonte'],
                territorio=form.cleaned_data['territorio']
            )
            return redirect('proyecto_detalle')





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

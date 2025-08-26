from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm
from haapar_unla_app.models import Tema, Variable, Subsistema
from django.contrib.auth.models import User

@login_required
def crear_reporte(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        horizonte = request.POST.get('horizonte')
        territorio = request.POST.get('territorio')

        #user = User.objects.get(username='Y')
        
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

def inicio(request):
    return render(request, 'haapar_unla_app/crear-reporte.html')


def listar_proyectos(request):
    temas = Tema.objects.filter(user=request.user,activo=True)
    return render(request, 'haapar_unla_app/listar-proyectos.html', {'temas': temas})


def proyecto_detalle(request, tema_id):
    tema = Tema.objects.get(id_tema=tema_id)
    return render(request, 'haapar_unla_app/proyecto-detalle.html', {'tema': tema})


def variable_detalle(request):
    variables = Variable.objects.filter(activo=True)
    return render(request, 'haapar_unla_app/variable-detalle.html' , {"variables": variables})

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
        
        Variable.objects.create(nombre=nombre, nombre_corto=nombre_corto, descripcion=descripcion, tipo=tipo,subsistema=subsistema)
        return redirect("variable_detalle")
    return render(request, "haapar_unla_app/crear-variable.html")


def registro(request):
    """
    Gestiona el registro de nuevos usuarios en la aplicación.

    GET: Muestra el formulario de registro.
    POST: Procesa el envío del formulario, valida las contraseñas,
          crea el usuario, lo autentica e inicia sesión, o muestra errores.
    """
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Los datos son válidos, crea el usuario
            user = form.save()
            login(request, user)
            return redirect("inicio")
        else:
            # El formulario no es válido, renderiza la plantilla con los errores
            return render(request, 'haapar_unla_app/autenticacion/signup.html', {
                'form': form,
            })
    else:
        # Si la solicitud es GET, creamos una instancia vacía del formulario
        form = SignUpForm()
        return render(request, 'haapar_unla_app/autenticacion/signup.html', {
            'form': form
        })


def cerrar_sesion(request):
    logout(request)
    return redirect("inicio")


def iniciar_sesion(request):
    """
    Gestiona el inicio de sesión de usuarios en la aplicación.

    GET: Muestra el formulario de inicio de sesión.
    POST: Procesa el envío del formulario, autentica al usuario e inicia sesión,
          o muestra un mensaje de error si las credenciales son incorrectas.
    """
    if request.method == 'GET':
        # Si la solicitud es GET, simplemente mostramos el formulario vacío
        return render(request, "haapar_unla_app/autenticacion/signin.html", {
            'form': AuthenticationForm() # Pasamos una instancia del formulario de autenticación
        })
    else: # Si la solicitud es POST (se envió el formulario)
        # print(request.POST)
        # Intentamos autenticar al usuario usando las credenciales enviadas
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        
        if user is None:
            # Si authenticate devuelve None, significa que las credenciales son incorrectas
            return render(request, "haapar_unla_app/autenticacion/signin.html", {
                'form': AuthenticationForm(),
                'error': 'El usuario o la contraseña son incorrectas.'
            })
        else:
            # Si authenticate devuelve un objeto de usuario, las credenciales son correctas
            login(request, user)
            return redirect('inicio')


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




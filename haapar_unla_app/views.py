from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from .forms import SignUpForm

def inicio(request):
    return render(request, 'haapar_unla_app/index.html')


def about(request):
    return render(request, 'haapar_unla_app/about.html')


def blog_details(request):
    return render(request, 'haapar_unla_app/blog-details.html')


def blog(request):
    return render(request, 'haapar_unla_app/blog.html')


def crear_reporte(request):
    return render(request, 'haapar_unla_app/crear-reporte.html')


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

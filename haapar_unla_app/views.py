from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError


def inicio(request):
    return render(request, 'haapar_unla_app/index.html')


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


def registro(request):
    """
    Gestiona el registro de nuevos usuarios en la aplicación.

    GET: Muestra el formulario de registro.
    POST: Procesa el envío del formulario, valida las contraseñas,
          crea el usuario, lo autentica e inicia sesión, o muestra errores.
    """
    if request.method == 'GET':
        return render(request, 'haapar_unla_app/autenticacion/signup.html', {
            'form': UserCreationForm
        })
    else:
        if request.POST['password1'] == request.POST['password2']:
            # Registro de Usuarios
            try:
                user = User.objects.create_user(
                    username=request.POST["username"], password=request.POST["password1"])
                user.save()
                login(request, user)
                return redirect("inicio")
            except IntegrityError:
                return render(request, 'haapar_unla_app/autenticacion/signup.html', {
                    'form': UserCreationForm,
                    'error': "El usuario ya existe"
                })
        return render(request, 'haapar_unla_app/autenticacion/signup.html', {
            'form': UserCreationForm,
            'error': "Contraseña no coincide"
        })

def cerrar_sesion(request):
    logout(request)
    return redirect("inicio")

def iniciar_sesion(request):
    if request.method == 'GET':
        return render(request, "haapar_unla_app/autenticacion/signin.html", {
            'form': AuthenticationForm
        })
    else:
        # print(request.POST)
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        
        if user is None:
            return render(request, "haapar_unla_app/autenticacion/signin.html", {
            'form': AuthenticationForm,
            'error': 'Usuario o contraseña es incorrecto'
        })
        else:
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

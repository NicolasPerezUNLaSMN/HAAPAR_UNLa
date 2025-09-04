from django.contrib.auth import logout
from haapar_unla_app.dominio.puertos.salida.usuario_repositorio import UsuarioRepositorio

class CerrarSesion:
    def __init__(self, repositorio: UsuarioRepositorio):
        self.repositorio = repositorio

    def ejecutar(self, request) -> None:
        # Funcion de Django
        logout(request)
    
        print(f"Sesión cerrada para el usuario")
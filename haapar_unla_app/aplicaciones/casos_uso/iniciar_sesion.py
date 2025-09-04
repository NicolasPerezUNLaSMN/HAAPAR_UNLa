from haapar_unla_app.dominio.entidades.usuario import Usuario
from haapar_unla_app.dominio.puertos.salida.usuario_repositorio import UsuarioRepositorio
from django.contrib.auth import authenticate

class IniciarSesion:
    def __init__(self, repositorio: UsuarioRepositorio):
        self.repositorio = repositorio

    def ejecutar(self, username: str, password: str) -> Usuario:
        # 1. Primero autenticar con Django (para verificar password)
        user_django = authenticate(username=username, password=password)
        if not user_django:
            raise ValueError("Credenciales incorrectas")
        
        # 2. Luego obtener tu entidad desde el repositorio
        usuario_entidad = self.repositorio.obtener_por_username(username)
        if not usuario_entidad:
            raise ValueError("Usuario no encontrado")
        
        return usuario_entidad
    

from haapar_unla_app.dominio.entidades.usuario import Usuario
from haapar_unla_app.dominio.puertos.salida.usuario_repositorio import UsuarioRepositorio

class RegistrarUsuario:
    def __init__(self, repositorio: UsuarioRepositorio):
        self.repositorio = repositorio

    def ejecutar(self, username: str, first_name: str, last_name: str, email: str, password: str, grupo_id: int = 1) -> Usuario:
       
        # 1. Crear entidad
        usuario = Usuario(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            grupo_id=grupo_id
        )
        
        # 2. Validar reglas de negocio
        usuario.validar()
        
        # 3. Verificar email único
        if self.repositorio.existe_email(usuario.email):
            raise ValueError("El email ya está registrado")
        
        if self.repositorio.existe_username(usuario.username):
            raise ValueError("El nombre de usuario ya existe")
        
        # 4. Guardar
        return self.repositorio.guardar(usuario)
from abc import ABC, abstractmethod
from dominio.entidades.usuario import Usuario

class UsuarioService(ABC):
    @abstractmethod
    def registrar_usuario(self, nombre: str, email: str, password: str) -> Usuario:
        pass
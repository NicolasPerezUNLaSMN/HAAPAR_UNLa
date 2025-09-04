#Interfaz abstracta que define cómo la aplicación se comunica con el almacenamiento de datos
from abc import ABC, abstractmethod
from haapar_unla_app.dominio.entidades.usuario import Usuario


class UsuarioRepositorio(ABC):
    @abstractmethod
    def guardar(self, usuario: Usuario) -> Usuario:
        pass

    @abstractmethod
    def obtener_por_id(self, id: int) -> Usuario:
        pass

    @abstractmethod
    def obtener_por_email(self, email: str) -> Usuario:
        pass

    @abstractmethod
    def obtener_por_username(self, username: str) -> Usuario:
        pass

    @abstractmethod
    def existe_email(self, email: str) -> bool:
        pass

    @abstractmethod
    def existe_username(self, username: str) -> bool:
        pass

    @abstractmethod
    def verificar_password(self, username: str, password_plana: str) -> bool:
        pass


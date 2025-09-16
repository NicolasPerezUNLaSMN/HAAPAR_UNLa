from abc import ABC, abstractmethod
from haapar_unla_app.dominio.entidades.tema import Tema

class TemaRepositorio(ABC):
    @abstractmethod
    def guardar(self, tema:Tema) -> Tema:
        pass

"""
    @abstractmethod
    def obtener_por_id_tema(self, id: int) -> Tema:
        pass

    @abstractmethod
    def obtener_por_id_usuario(self, id: int) -> Tema:
        pass
"""

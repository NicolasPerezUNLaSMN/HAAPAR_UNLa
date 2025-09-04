from haapar_unla_app.dominio.entidades.tema import Tema
from haapar_unla_app.dominio.puertos.salida.tema_repositorio import TemaRepositorio

class CrearTema:
    def __init__(self, repositorio: TemaRepositorio):
        self.repositorio = repositorio

    def crear(self, user_id: int, nombre: str, descripcion: str, 
                 horizonte: str, territorio: str) -> Tema:
        
        tema = Tema(
            usuario_id=user_id, 
            nombre=nombre,
            descripcion=descripcion,
            horizonte=horizonte,
            territorio=territorio,
            #activo = True
        )
        
        tema.validar()
        
        return self.repositorio.guardar(tema)
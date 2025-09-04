from haapar_unla_app.dominio.puertos.salida.tema_repositorio import TemaRepositorio
from haapar_unla_app.dominio.entidades.tema import Tema as TemaEntidad
from haapar_unla_app.models import Tema as TemaModel

class TemaRepositorioDB(TemaRepositorio):

    def guardar (self, tema_entidad: TemaEntidad) -> TemaEntidad:
        try:
            tema_db = TemaModel.objects.create(
                nombre = tema_entidad.nombre,
                user_id = tema_entidad.usuario_id,
                descripcion = tema_entidad.descripcion,
                horizonte = tema_entidad.horizonte,
                territorio = tema_entidad.territorio,
                #activo = tema_entidad.activo
            )

            return self._convertir_a_entidad(tema_db)
        
        except Exception as e:
            raise ValueError(f"Error al guardar el Tema: {str(e)}")
            

    def _convertir_a_entidad(self, tema_db: TemaModel) -> TemaEntidad:
        return TemaEntidad(
            id_tema=tema_db.id_tema,
            nombre=tema_db.nombre,
            usuario_id=tema_db.user.id,
            descripcion=tema_db.descripcion,
            horizonte=tema_db.horizonte,
            territorio=tema_db.territorio,
            #activo = tema_db.activo
        )
import logging
from haapar_unla_app.dominio.puertos.salida.usuario_repositorio import UsuarioRepositorio
from haapar_unla_app.dominio.entidades.usuario import Usuario as UsuarioEntidad
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.hashers import check_password

# Configuramos el logger
logger = logging.getLogger(__name__)

UsuarioModel = get_user_model()

class UsuarioRepositorioDB(UsuarioRepositorio):

    def guardar(self, usuario_entidad: UsuarioEntidad):
        
        try:
            user_model = UsuarioModel.objects.create_user(
                username=usuario_entidad.username,  
                email=usuario_entidad.email,
                first_name=usuario_entidad.first_name,  
                last_name=usuario_entidad.last_name,
                password=usuario_entidad.password,
                grupo_id=usuario_entidad.grupo_id  
            )
            return self._convertir_a_entidad(user_model)
        except Exception as e:
            raise ValueError(f"Error al guardar usuario: {str(e)}")

    def obtener_por_id(self, id: int) -> UsuarioEntidad:
        try:
            usuario_db = UsuarioModel.objects.get(id=id)
            return self._convertir_a_entidad(usuario_db)
        except ObjectDoesNotExist:
            return None
        except Exception as e:
            raise ValueError(f"Error al obtener usuario por ID: {str(e)}")

    def obtener_por_email(self, email: str) -> UsuarioEntidad:
        try:
            usuario_db = UsuarioModel.objects.get(email=email)
            return self._convertir_a_entidad(usuario_db)
        except ObjectDoesNotExist:
            return None
        except Exception as e:
            raise ValueError(f"Error al obtener usuario por email: {str(e)}")

    
    def obtener_por_username(self, username: str) -> UsuarioEntidad:
        try:
            usuario_db = UsuarioModel.objects.get(username=username)
            return self._convertir_a_entidad(usuario_db)
        except ObjectDoesNotExist:
            return None
        except Exception as e:
            raise ValueError(f"Este usuario no se encuentra registrado : {str(e)}")
        
    
    
    def _convertir_a_entidad(self, usuario_db) -> UsuarioEntidad:
        """Convierte el modelo Django a entidad de dominio"""
        
        # Usamos un log de nivel debug sin exponer información sensible como la contraseña
        logger.debug(f"Convirtiendo usuario ID {usuario_db.id} a entidad de dominio.")
        
        return UsuarioEntidad(
            id=usuario_db.id,
            username=usuario_db.username,
            first_name=usuario_db.first_name,
            last_name=usuario_db.last_name,
            email=usuario_db.email,
            password=usuario_db.password,
            grupo_id=getattr(usuario_db, 'grupo_id', 1)
        )
    
    def existe_email(self, email: str) -> bool:
        return UsuarioModel.objects.filter(email=email).exists()
    

    def existe_username(self, username: str) -> bool:
        return UsuarioModel.objects.filter(username=username).exists()
    

    def verificar_password(self, username: str, password_plana: str) -> bool:
        usuario_db = UsuarioModel.objects.get(username=username)
        return check_password(password_plana, usuario_db.password)
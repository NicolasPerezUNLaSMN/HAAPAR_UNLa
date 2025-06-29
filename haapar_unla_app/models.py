from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True, verbose_name='ID Rol')
    nombre = models.CharField(max_length=15) #Roles --> creador / modificador
    
    def __str__(self):
        return self.nombre



class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True, verbose_name='ID Usuario')
    nombre = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
   
    
    def __str__(self):
        return self.email
    
    def set_password(self, raw_password):
        """Encripta la contraseña"""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Verifica la contraseña"""
        return check_password(raw_password, self.password)

    @classmethod
    def authenticate(cls, email=None, password=None):
        """Método básico de autenticación"""
        try:
            user = cls.objects.get(email=email)
            if user.check_password(password):
                return user
        except cls.DoesNotExist:
            return None
        return None



class UsuarioRol(models.Model):
    id_usuario_rol = models.AutoField(primary_key=True, db_column='id_usuario_rol')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='id_usuario')
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, db_column='id_rol')
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self):
        return f"{self.usuario} - {self.rol}"



class Tema(models.Model):
    id_tema = models.AutoField(primary_key=True, verbose_name='ID Tema')
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    horizonte = models.CharField(max_length=50)
    territorio = models.CharField(max_length=255)
    
    
    def __str__(self):
        return self.nombre



class Sistema(models.Model):
    id_sistema = models.AutoField(primary_key=True, verbose_name='ID Sistema')
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    
    
    def __str__(self):
        return self.nombre



class Subsistema(models.Model):
    id_subsistema = models.AutoField(primary_key=True, verbose_name='ID Subsistema')
    sistema = models.ForeignKey(Sistema, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()

    
    def __str__(self):
        return self.nombre



class TendenciaExterna(models.Model):
    id_tendenciaExterna = models.AutoField(primary_key=True, verbose_name='ID Tendencia Externa')
    nombre = models.CharField(max_length=255)
    nombre_corto = models.CharField(max_length=50)

    subsistema = models.ForeignKey(Subsistema, on_delete=models.CASCADE)

    TIPO_PESTEL_CHOICES = [
        ('P', 'Político'),
        ('E', 'Económico'),
        ('S', 'Social'),
        ('T', 'Tecnológico'),
        ('L', 'Legal'),
        ('M', 'Medioambiental'),
    ]
    
    tipo_pestel = models.CharField(max_length=50, choices=TIPO_PESTEL_CHOICES)
    tipo_dato = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=255)
    
    def __str__(self):
        return self.nombre



class Variable(models.Model):
    id_variable = models.AutoField(primary_key=True, verbose_name='ID Variable')
    subsistema = models.ForeignKey(Subsistema, on_delete=models.CASCADE)
    forma_medicion = models.TextField()
    descripcion = models.CharField(max_length=255)
    nombre = models.CharField(max_length=255)
    nombre_corto = models.CharField(max_length=50)
    tipo = models.CharField(max_length=50)
    
    
    def __str__(self):
        return self.nombre



class Indicador(models.Model):
    id_indicador = models.AutoField(primary_key=True, verbose_name='ID Indicador')

    variable = models.ForeignKey(Variable, on_delete=models.CASCADE)
    tendencia = models.ForeignKey(TendenciaExterna, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    nombre_corto = models.CharField(max_length=50)
    descripcion = models.TextField()
    formula = models.TextField()
    
    
    def __str__(self):
        return self.nombre



class VariableTendencia(models.Model):
    id_variableTendencia = models.AutoField(primary_key=True, verbose_name='ID Variable-Tendencia')

    variable = models.ForeignKey(Variable, on_delete=models.CASCADE)
    tendencia = models.ForeignKey(TendenciaExterna, on_delete=models.CASCADE)
    impacto = models.DecimalField(max_digits=5, decimal_places=2)
    
    def __str__(self):
        return f"{self.variable} - {self.tendencia}"



class Influencia(models.Model):
    id_influencia = models.AutoField(primary_key=True, verbose_name='ID Influencia')

    variable_origen = models.ForeignKey(Variable, on_delete=models.CASCADE, related_name='influencias_origen')
    variable_destino = models.ForeignKey(Variable, on_delete=models.CASCADE, related_name='influencias_destino')
    valor = models.DecimalField(max_digits=5, decimal_places=2)
    
    def __str__(self):
        return f"{self.variable_origen} → {self.variable_destino}"



class Evaluacion(models.Model):
    id_evaluacion = models.AutoField(primary_key=True, verbose_name='ID Evaluacion')

    variable = models.ForeignKey(Variable, on_delete=models.CASCADE)
    usuario_creacion = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='usuario_creador')
    usuario_modificacion = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='usuario_mod')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    importancia = models.DecimalField(max_digits=5, decimal_places=2)
    incertidumbre = models.DecimalField(max_digits=3, decimal_places=2)
    
    
    def __str__(self):
        return f"Evaluación de {self.variable}"
    


class ActorClave(models.Model):
    id_actor_clave = models.AutoField(primary_key=True, verbose_name='ID Actor Clave')
    subsistema = models.ForeignKey(
        'Subsistema',
        on_delete=models.CASCADE,
        db_column='id_subsistema',
        verbose_name='Subsistema relacionado'
    )
    nombre = models.CharField(max_length=255)
    puesto = models.CharField(max_length=255)
    descripcion = models.TextField()
    
    def __str__(self):
        return f"{self.nombre}"
    


class RelacionActor(models.Model):
    id_relacion = models.AutoField(primary_key=True, verbose_name='ID Relación')
    actor_fuente = models.ForeignKey(
        ActorClave,
        on_delete=models.CASCADE,
        related_name='relaciones_como_fuente',
        db_column='id_actor_fuente',
        verbose_name='Actor origen'
    )
    actor_destino = models.ForeignKey(
        ActorClave,
        on_delete=models.CASCADE,
        related_name='relaciones_como_destino',
        db_column='id_actor_destino',
        verbose_name='Actor destino'
    )
    influencia = models.IntegerField(
        Influencia,
        on_delete=models.CASCADE
    )

    
    def __str__(self):
        return f"{self.actor_fuente} → {self.actor_destino} (Influencia: {self.influencia})"
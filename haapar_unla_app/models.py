from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.contrib.auth.hashers import make_password

class Task(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    datecompleted = models.DateTimeField(null=True, blank=True)
    important = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Usuario(AbstractUser):
    grupo_id = models.IntegerField(default=1)
    
    username = models.CharField(max_length=150, unique=True, blank=False, null=True)
    
    USERNAME_FIELD = 'username'  # Campo que se usa para login
    REQUIRED_FIELDS = ['email']  # Campos que pedirá al crear superusuario
    
    class Meta:
        db_table = 'haapar_unla_app_usuario'

    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

class Tema(models.Model):
    id_tema = models.AutoField(primary_key=True, verbose_name='ID Tema')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    horizonte = models.CharField(max_length=50)
    territorio = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)
    
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
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class PESTEL(models.Model):
    PESTEL_CHOICES = [
        ('P', 'Político'),
        ('EC', 'Económico'),
        ('S', 'Social'),
        ('T', 'Tecnológico'),
        ('EO', 'Ecológico'),
        ('L', 'Legal'),
    ]

    tipo = models.CharField(max_length=2, choices=PESTEL_CHOICES)

    def __str__(self):
        return self.get_tipo_display()

class Variable(models.Model):
    id_variable = models.AutoField(primary_key=True, verbose_name='ID Variable')
    subsistema = models.ForeignKey(Subsistema, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    nombre_corto = models.CharField(max_length=50)
    descripcion = models.TextField()
    activo = models.BooleanField(default=True)
    
    INTERNA_EXTERNA_CHOICES = [
        ('I', 'Interna'),
        ('E', 'Externa'),
    ]
    tipo = models.CharField(max_length=1, choices=INTERNA_EXTERNA_CHOICES)
    pestels = models.ManyToManyField('PESTEL')
    
    def __str__(self):
        return self.nombre

class IndicadorVariable(models.Model):
    id_indicador = models.AutoField(primary_key=True, verbose_name='ID Indicador')
    variable = models.ForeignKey(Variable, on_delete=models.CASCADE)
    nombre_corto = models.CharField(max_length=50)
    descripcion = models.TextField()
    formula = models.TextField()
    
    def __str__(self):
        return self.nombre_corto
    
    
class Influencia(models.Model):
    id_influencia = models.AutoField(primary_key=True, verbose_name='ID Influencia')
    valor = models.DecimalField(max_digits=5, decimal_places=2)
    variable_origen = models.ForeignKey(Variable, on_delete=models.CASCADE, related_name='influencias_origen')
    variable_destino = models.ForeignKey(Variable, on_delete=models.CASCADE, related_name='influencias_destino')
    
    def __str__(self):
        return f"{self.variable_origen} → {self.variable_destino}"

class TendenciaExterna(models.Model):
    id_tendencia_externa = models.AutoField(primary_key=True, verbose_name='ID Tendencia Externa')
    subsistema= models.ForeignKey(Subsistema, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    nombre_corto = models.CharField(max_length=50)
    tipo_dato = models.CharField(max_length=50)
    descripcion = models.TextField()
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre

class IndicadorTendencia(models.Model):
    id_indicador_tendencia = models.AutoField(primary_key=True, verbose_name='ID Indicador')
    tendencia_externa = models.ForeignKey(TendenciaExterna, on_delete=models.CASCADE)
    nombre_corto = models.CharField(max_length=50)
    descripcion = models.TextField()
    formula = models.TextField()
    
    def __str__(self):
        return self.nombre_corto


class VariableTendencia(models.Model):
    id_variable_tendencia = models.AutoField(primary_key=True, verbose_name='ID Variable-Tendencia')

    variable = models.ForeignKey(Variable, on_delete=models.CASCADE)
    tendencia = models.ForeignKey(TendenciaExterna, on_delete=models.CASCADE)
    impacto = models.DecimalField(max_digits=5, decimal_places=2)
    
    def __str__(self):
        return f"{self.variable} - {self.tendencia}"


class Evaluacion(models.Model):
    id_evaluacion = models.AutoField(primary_key=True, verbose_name='ID Evaluacion')
    importancia = models.IntegerField(verbose_name='Importancia', choices=[(i, i) for i in range(0, 11)])
    incertidumbre = models.IntegerField(verbose_name='Incertidumbre', choices=[(i, i) for i in range(0, 11)])
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    variable = models.ForeignKey(Variable, on_delete=models.CASCADE)
    usuario_creador = models.ForeignKey(
        settings.AUTH_USER_MODEL,  
        on_delete=models.CASCADE, 
        related_name='usuario_creador'
    )
    usuario_modificador = models.ForeignKey(
        settings.AUTH_USER_MODEL,  
        on_delete=models.CASCADE,
        related_name='usuario_modificador'
    )
    
    def __str__(self):
        return f"Evaluación de {self.variable}"
    
class ActorClave(models.Model):
    id_actor_clave = models.AutoField(primary_key=True, verbose_name='ID Actor Clave')
    subsistema = models.ForeignKey(Subsistema, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    puesto = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre

class RelacionActor(models.Model):
    actor_clave = models.ForeignKey(ActorClave, on_delete=models.CASCADE, related_name='actor_fuente')
    subsistema = models.ForeignKey(Subsistema, on_delete=models.CASCADE)
    influencia = models.IntegerField()

    def __str__(self):
        return f"{self.actor_clave} - {self.subsistema} (Influencia: {self.influencia})"
from django.db import models
from django.contrib.auth.models import User

class Tema(models.Model):
    id_tema = models.AutoField(primary_key=True, verbose_name='ID Tema')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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
    # ESTO ES LO QUE FALTABA
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE, related_name='tendencias_externas')
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
    usuario_creador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usuario_creador')
    usuario_modificador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usuario_mod')
    
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

##Clase de actor
    
class Actor(models.Model):
    TIPO_INFLUENCIA = [
        (1, 'Baja'),
        (2, 'Media'),
        (3, 'Alta'),
    ]
    
    subsistema = models.ForeignKey(Subsistema, on_delete=models.CASCADE)
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    puesto = models.CharField(max_length=100)
    emite = models.BooleanField(default=False)
    recibe = models.BooleanField(default=False)
    influencia = models.IntegerField(choices=TIPO_INFLUENCIA, default=2)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre

class RelacionActor(models.Model):
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE)  # Cambiado de actor_clave a actor
    subsistema = models.ForeignKey(Subsistema, on_delete=models.CASCADE)
    influencia = models.IntegerField(default=2)
    
    def __str__(self):
        return f"{self.actor} - {self.subsistema}"
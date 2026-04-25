from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg 

class Tema(models.Model):
    id_tema = models.AutoField(primary_key=True, verbose_name='ID Tema')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    horizonte = models.CharField(max_length=50)
    territorio = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)
    
    # nuevo campo
    colaboradores = models.ManyToManyField(
        User,
        related_name="temas_colaborando",
        blank=True
    )
    
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
    
    def promedio_importancia(self):
        return self.evaluaciones.aggregate(Avg('importancia'))['importancia__avg'] or 0

    def promedio_incertidumbre(self):
        return self.evaluaciones.aggregate(Avg('incertidumbre'))['incertidumbre__avg'] or 0
    
class EvaluacionVariable(models.Model):
    variable = models.ForeignKey(
        Variable,
        on_delete=models.CASCADE,
        related_name='evaluaciones'
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    importancia = models.IntegerField(choices=[(i, i) for i in range(0, 11)])
    incertidumbre = models.IntegerField(choices=[(i, i) for i in range(0, 11)])

    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('variable', 'usuario')

    def __str__(self):
        return f"{self.variable.nombre} - {self.usuario or 'IA'}"

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
    
    def promedio_importancia(self):
        return self.evaluaciones.aggregate(Avg('importancia'))['importancia__avg'] or 0

    def promedio_incertidumbre(self):
        return self.evaluaciones.aggregate(Avg('incertidumbre'))['incertidumbre__avg'] or 0
    
class EvaluacionTendencia(models.Model):
    tendencia = models.ForeignKey(
        TendenciaExterna,
        on_delete=models.CASCADE,
        related_name='evaluaciones'
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    importancia = models.IntegerField(choices=[(i, i) for i in range(0, 11)])
    incertidumbre = models.IntegerField(choices=[(i, i) for i in range(0, 11)])

    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tendencia', 'usuario')

    def __str__(self):
        return f"{self.tendencia.nombre} - {self.usuario or 'IA'}"

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


class Historial(models.Model):
    ACCIONES = [
        ('CREADO', 'Creado'),
        ('AGREGADO', 'Agregado'),
        ('ELIMINADO', 'Eliminado'),
        ('MODIFICADO', 'Modificado'),
        ('EVALUACION', 'Evaluación'),
    ]
    id_historial = models.AutoField(primary_key=True, verbose_name='ID Historial')
    fecha = models.DateTimeField(auto_now_add=True)
    
    variable = models.ForeignKey(Variable, on_delete=models.SET_NULL, null=True, blank=True)
    tendencia = models.ForeignKey(TendenciaExterna, on_delete=models.SET_NULL, null=True, blank=True)
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    accion = models.CharField(max_length=20, choices=ACCIONES)
    
    detalles = models.TextField(null=True, blank=True) 
    
    def __str__(self):
        if self.usuario:
            return f"{self.accion} - {self.usuario}"
        return f"{self.accion} - IA"
    

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

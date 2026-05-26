from django.contrib.auth.models import User
from django.db import models
from django.db.models import Avg

from .proyectos import Subsistema
from .variables import Variable


class TendenciaExterna(models.Model):
    id_tendencia_externa = models.AutoField(
        primary_key=True, verbose_name="ID Tendencia Externa"
    )
    subsistema = models.ForeignKey(Subsistema, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    nombre_corto = models.CharField(max_length=50)
    tipo_dato = models.CharField(max_length=50)
    descripcion = models.TextField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    def promedio_importancia(self):
        return self.evaluaciones.aggregate(Avg("importancia"))["importancia__avg"] or 0

    def promedio_incertidumbre(self):
        return (
            self.evaluaciones.aggregate(Avg("incertidumbre"))["incertidumbre__avg"] or 0
        )


class EvaluacionTendencia(models.Model):
    tendencia = models.ForeignKey(
        TendenciaExterna, on_delete=models.CASCADE, related_name="evaluaciones"
    )
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    importancia = models.IntegerField(choices=[(i, i) for i in range(0, 11)])
    incertidumbre = models.IntegerField(choices=[(i, i) for i in range(0, 11)])
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tendencia", "usuario")

    def __str__(self):
        return f"{self.tendencia.nombre} - {self.usuario or 'IA'}"


class IndicadorTendencia(models.Model):
    id_indicador_tendencia = models.AutoField(
        primary_key=True, verbose_name="ID Indicador"
    )
    tendencia_externa = models.ForeignKey(TendenciaExterna, on_delete=models.CASCADE)
    nombre_corto = models.CharField(max_length=50)
    descripcion = models.TextField()
    formula = models.TextField()

    def __str__(self):
        return self.nombre_corto


class VariableTendencia(models.Model):
    id_variable_tendencia = models.AutoField(
        primary_key=True, verbose_name="ID Variable-Tendencia"
    )
    variable = models.ForeignKey(Variable, on_delete=models.CASCADE)
    tendencia = models.ForeignKey(TendenciaExterna, on_delete=models.CASCADE)
    impacto = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.variable} - {self.tendencia}"

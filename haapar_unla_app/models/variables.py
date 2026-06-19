from django.contrib.auth.models import User
from django.db import models
from django.db.models import Avg

from .proyectos import Subsistema


class PESTEL(models.Model):
    PESTEL_CHOICES = [
        ("P", "Político"),
        ("EC", "Económico"),
        ("S", "Social"),
        ("T", "Tecnológico"),
        ("EO", "Ecológico"),
        ("L", "Legal"),
    ]
    tipo = models.CharField(max_length=2, choices=PESTEL_CHOICES)

    def __str__(self):
        return self.get_tipo_display()


class Variable(models.Model):
    id_variable = models.AutoField(primary_key=True, verbose_name="ID Variable")
    subsistema = models.ForeignKey(Subsistema, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    nombre_corto = models.CharField(max_length=50)
    descripcion = models.TextField()
    activo = models.BooleanField(default=True)

    INTERNA_EXTERNA_CHOICES = [
        ("I", "Interna"),
        ("E", "Externa"),
    ]
    tipo = models.CharField(max_length=1, choices=INTERNA_EXTERNA_CHOICES)
    pestels = models.ManyToManyField("PESTEL")

    def __str__(self):
        return self.nombre

    def promedio_importancia(self):
        return self.evaluaciones.aggregate(Avg("importancia"))["importancia__avg"] or 0

    def promedio_incertidumbre(self):
        return (
            self.evaluaciones.aggregate(Avg("incertidumbre"))["incertidumbre__avg"] or 0
        )


class EvaluacionVariable(models.Model):
    variable = models.ForeignKey(
        Variable, on_delete=models.CASCADE, related_name="evaluaciones"
    )
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    importancia = models.IntegerField(choices=[(i, i) for i in range(0, 11)])
    incertidumbre = models.IntegerField(choices=[(i, i) for i in range(0, 11)])
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("variable", "usuario")
        indexes = [
            models.Index(fields=["variable", "usuario"]),
        ]

    def __str__(self):
        return f"{self.variable.nombre} - {self.usuario or 'IA'}"


class IndicadorVariable(models.Model):
    id_indicador = models.AutoField(primary_key=True, verbose_name="ID Indicador")
    variable = models.ForeignKey(Variable, on_delete=models.CASCADE)
    nombre_corto = models.CharField(max_length=50)
    descripcion = models.TextField()
    formula = models.TextField()

    def __str__(self):
        return self.nombre_corto


class Influencia(models.Model):
    id_influencia = models.AutoField(primary_key=True, verbose_name="ID Influencia")
    valor = models.DecimalField(max_digits=5, decimal_places=2)
    variable_origen = models.ForeignKey(
        Variable, on_delete=models.CASCADE, related_name="influencias_origen"
    )
    variable_destino = models.ForeignKey(
        Variable, on_delete=models.CASCADE, related_name="influencias_destino"
    )

    class Meta:
        indexes = [
            models.Index(fields=["variable_origen", "variable_destino"]),
        ]

    def __str__(self):
        return f"{self.variable_origen} → {self.variable_destino}"

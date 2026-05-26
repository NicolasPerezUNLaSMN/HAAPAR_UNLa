from django.contrib.auth.models import User
from django.db import models

from .proyectos import Tema
from .tendencias import TendenciaExterna
from .variables import Variable


class Historial(models.Model):
    ACCIONES = [
        ("CREADO", "Creado"),
        ("AGREGADO", "Agregado"),
        ("ELIMINADO", "Eliminado"),
        ("MODIFICADO", "Modificado"),
        ("EVALUACION", "Evaluación"),
    ]
    id_historial = models.AutoField(primary_key=True, verbose_name="ID Historial")
    fecha = models.DateTimeField(auto_now_add=True)

    variable = models.ForeignKey(
        Variable, on_delete=models.SET_NULL, null=True, blank=True
    )
    tendencia = models.ForeignKey(
        TendenciaExterna, on_delete=models.SET_NULL, null=True, blank=True
    )
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    accion = models.CharField(max_length=20, choices=ACCIONES)
    detalles = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["variable"]),
            models.Index(fields=["fecha"]),
        ]

    def __str__(self):
        if self.usuario:
            return f"{self.accion} - {self.usuario}"
        return f"{self.accion} - IA"


class IAInteraction(models.Model):
    id_interaccion = models.AutoField(
        primary_key=True, verbose_name="ID Interacción IA"
    )
    fecha = models.DateTimeField(auto_now_add=True)
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE, null=True, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    prompt = models.TextField()
    respuesta = models.TextField(null=True, blank=True)
    success = models.BooleanField(default=False)
    error = models.TextField(null=True, blank=True)

    def __str__(self):
        estado = "OK" if self.success else "ERROR"
        return f"IA {estado} - {self.fecha.strftime('%Y-%m-%d %H:%M:%S')}"

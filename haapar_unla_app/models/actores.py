from django.db import models

from .proyectos import Subsistema


class ActorClave(models.Model):
    id_actor_clave = models.AutoField(primary_key=True, verbose_name="ID Actor Clave")
    subsistema = models.ForeignKey(Subsistema, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    puesto = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class RelacionActor(models.Model):
    actor_clave = models.ForeignKey(
        ActorClave, on_delete=models.CASCADE, related_name="actor_fuente"
    )
    subsistema = models.ForeignKey(Subsistema, on_delete=models.CASCADE)
    influencia = models.IntegerField()

    def __str__(self):
        return f"{self.actor_clave} - {self.subsistema} (Influencia: {self.influencia})"

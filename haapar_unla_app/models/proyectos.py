from django.contrib.auth.models import User
from django.db import models


class Tema(models.Model):
    id_tema = models.AutoField(primary_key=True, verbose_name="ID Tema")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    horizonte = models.CharField(max_length=50)
    territorio = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)

    colaboradores = models.ManyToManyField(
        User, related_name="temas_colaborando", blank=True
    )

    def __str__(self):
        return self.nombre


class Sistema(models.Model):
    id_sistema = models.AutoField(primary_key=True, verbose_name="ID Sistema")
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre


class Subsistema(models.Model):
    id_subsistema = models.AutoField(primary_key=True, verbose_name="ID Subsistema")
    sistema = models.ForeignKey(Sistema, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

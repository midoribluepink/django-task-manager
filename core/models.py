from django.db import models

class Tarea(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    fecha_limite = models.DateField(null=True, blank=True)
    completada = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.titulo[:25]}: {self.completada}"
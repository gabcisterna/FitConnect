from django.db import models

# Create your models here.
class Room(models.Model):
    name = models.CharField(max_length=80, unique=True)
    capacity = models.PositiveIntegerField(default=20)

    def __str__(self):
        return f"{self.name} (cap: {self.capacity})"


class ClassType(models.Model):
    """
    Tipo de clase (ej: Funcional, Spinning, Yoga).
    Todas las clases duran 60 minutos (fijo).
    """
    name = models.CharField(max_length=80, unique=True)
    # Fijamos duración a 60 y no editable para hacerla inmutable desde el admin
    duration_min = models.PositiveIntegerField(default=60, editable=False)
    default_capacity = models.PositiveIntegerField(default=20)

    def __str__(self):
        return self.name


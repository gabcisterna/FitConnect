from datetime import timedelta, datetime, time, date
from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.
WEEKDAYS = [
    (0, "Lunes"), (1, "Martes"), (2, "Miércoles"),
    (3, "Jueves"), (4, "Viernes"), (5, "Sábado"), (6, "Domingo"),
]

class Room(models.Model):
    name = models.CharField(max_length=80, unique=True)
    capacity = models.PositiveIntegerField(default=20)

    def __str__(self):
        return f"{self.name} (cap: {self.capacity})"


class ClassType(models.Model):
    # Todas las clases duran 60 min (fijo)
    name = models.CharField(max_length=80, unique=True)
    duration_min = models.PositiveIntegerField(default=60, editable=False)
    default_capacity = models.PositiveIntegerField(default=20)

    def __str__(self):
        return self.name


class ClassSchedule(models.Model):
    """
    Plantilla semanal: (weekday + start_time) para un tipo de clase en una sala.
    Capacidad efectiva SIEMPRE = min(Room.capacity, ClassType.default_capacity).
    """
    class_type = models.ForeignKey("ClassType", on_delete=models.PROTECT)
    room = models.ForeignKey("Room", on_delete=models.PROTECT)
    weekday = models.IntegerField(choices=WEEKDAYS)  # 0=Lun ... 6=Dom
    start_time = models.TimeField()

    # Capacidad efectiva (se autocalcula). Se guarda para visibilidad y auditoría.
    capacity = models.PositiveIntegerField(editable=False)

    # Permite pausar un horario sin borrarlo (no genera sesiones nuevas si está False)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("room", "weekday", "start_time")
        ordering = ["weekday", "start_time"]

    def compute_capacity(self) -> int:
        return min(self.room.capacity, self.class_type.default_capacity)

    @property
    def duration(self) -> timedelta:
        return timedelta(minutes=60)

    def clean(self):
        # Si aún no hay room/classtype no calculamos (pasa en admin al crear)
        if self.room_id and self.class_type_id:
            self.capacity = self.compute_capacity()
            if self.capacity == 0:
                raise ValidationError("La capacidad efectiva no puede ser 0.")

    def save(self, *args, **kwargs):
        if self.room_id and self.class_type_id:
            self.capacity = self.compute_capacity()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.class_type.name} • {self.get_weekday_display()} {self.start_time} • {self.room.name} ({self.capacity})"


class ClassSession(models.Model):
    """
    Instancia fechada (p.ej., 2025-09-24 16:30) generada desde un ClassSchedule.
    La capacidad se 'fotografía' del schedule al momento de crearla.
    """
    schedule = models.ForeignKey("ClassSchedule", on_delete=models.PROTECT, related_name="sessions")
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    capacity = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=[("scheduled", "Programada"), ("cancelled", "Cancelada")],
        default="scheduled",
    )

    class Meta:
        unique_together = ("schedule", "start_at")  # evita duplicados al generar
        ordering = ["start_at"]

    def clean(self):
        if self.capacity == 0:
            raise ValidationError("La capacidad de la sesión no puede ser 0.")
        if self.end_at <= self.start_at:
            raise ValidationError("La hora de fin debe ser mayor que la de inicio.")

    def __str__(self):
        return f"{self.schedule.class_type.name} @ {self.start_at:%Y-%m-%d %H:%M}"
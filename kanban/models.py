"""Modelo para tareas en el sistema Kanban."""
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from intranet.models import User, Ot


class Tarea(models.Model):
    """Modelo para tareas en el sistema Kanban."""
    STATUS_CHOICES = [
        ('todo', 'Por Hacer'),
        ('in_progress', 'En Progreso'),
        ('review', 'En Revisión'),
        ('done', 'Hecho'),
    ]
    PRIORITY_CHOICES = [
        ('high', 'Muy Urgente'),
        ('medium', 'Urgente'),
        ('low', 'Estable'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True)
    ot = models.ForeignKey(Ot, on_delete=models.CASCADE, null=True, blank=True)
    titulo = models.CharField(max_length=200, null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    estado = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='todo', null=True, blank=True)
    prioridad = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default='low', null=True, blank=True)
    vencimiento = models.DateTimeField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    editado = models.DateTimeField(auto_now=True)
    duracion = models.DurationField(null=True, blank=True)
    orden = models.PositiveIntegerField(default=0, null=False, blank=False)

    def __str__(self):
        return self.titulo


class Actividades(models.Model):
    """Registro de actividades"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True)
    ot = models.ForeignKey(Ot, models.DO_NOTHING, blank=True, null=True)
    tarea = models.ForeignKey(Tarea, models.DO_NOTHING, blank=True, null=True)
    inicio = models.DateTimeField(default=now, blank=True, null=True)
    fin = models.DateTimeField(blank=True, null=True)
    descripcion = models.CharField(max_length=2250, blank=True, null=True)
    comentario = models.CharField(max_length=10000, blank=True, null=True)

    def __str__(self):
        return str(self.inicio) + ' - ' + str(self.descripcion) + ' - ' + str(self.user)

    def total(self):
        """Total en horas y minutos, asegurando que el cálculo
        empieza a las 08:00 si inicio es antes de las 08:00"""
        if self.inicio and self.fin:

            # Calcular la diferencia entre inicio y fin
            diferencia = self.fin - self.inicio
            horas, segundos = divmod(diferencia.total_seconds(), 3600)
            minutos = segundos // 60
            return f"{int(horas):02}:{int(minutos):02}"
        return None

    def total_decimal(self):
        """Calcula la diferencia entre inicio y fin en formato decimal,
        asegurando que el cálculo empieza a las 08:00 si inicio es antes de las 08:00"""
        if self.inicio and self.fin:
            # Definir las 08:00 como la hora de inicio mínima
            hora_limite = self.inicio.replace(
                hour=8, minute=0, second=0, microsecond=0)
            # Si inicio es antes de las 08:00, ajustamos inicio a las 08:00
            if self.inicio < hora_limite:
                # Modificamos inicio a las 08:00
                inicio_ajustada = hora_limite
            else:
                # Si inicio es después de las 08:00, usamos inicio tal como está
                inicio_ajustada = self.inicio

            # Calcular la diferencia entre inicio ajustada y fin en segundos
            diferencia = self.fin - inicio_ajustada
            horas_decimales = diferencia.total_seconds() / 3600
            return round(horas_decimales, 2)
        return None


@receiver(post_save, sender=Ot)
def crear_tareas(sender, instance, created, **kwargs):
    """Crear tareas automáticamente según el tipo de OT"""
    if not created:
        return

    tareas_tipo_7 = [
        "A.1 Visita - Medicion",
        "Atención al Cliente"
        "Anteproyecto",
        "Arquitectura",
        "Diseño 3D",
        "Estructuras",
        "Electricas",
        "ETABS",
        "Gas Natural",
        "Redes",
        "Sanitarias",
        "Tutoria"
    ]

    tareas_otro = [
        "A.1 Visita - Medicion",
        "A.2 Tutoria",
        "B.2 Arquitectura - Distribución",
        "B.5 Ubicación - Localización",
        "B.9 Perimetrico",
        "C. Documentos",
        "D. Atención al Cliente",
        "C.13 Audiencia SUNARP",
        "D.18 Seguimiento Expediente",
        "D.17 Tramite",
    ]

    if instance.id_tipot and instance.id_tipot.id == 7:
        tareas = tareas_tipo_7
    else:
        tareas = tareas_otro

    for nombre_tarea in tareas:
        Tarea.objects.create(
            ot=instance,
            titulo=nombre_tarea
        )

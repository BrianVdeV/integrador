"""Models"""
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

# Create your models here.


class Area(models.Model):
    """Áreas de trabajo"""
    codigo = models.CharField(max_length=45, blank=True, null=True)
    nombre = models.CharField(max_length=25)

    def __str__(self):
        return str(self.nombre)


class Colaborador(models.Model):
    """ Datos de los colaboradores """
    CUENTA = [
        ('BCP', 'BCP'),
        ('CCI Banco de la Nación', 'CCI Banco de la Nación'),
        ('CCI BBVA', 'CCI BBVA'),
        ('CCI Interbank', 'CCI Interbank'),
        ('CCI Scotiabank', 'CCI Scotiabank'),
        ('Otro', 'Otro'),
    ]
    user = models.OneToOneField(
        User, models.DO_NOTHING, blank=True, null=True)
    area = models.ForeignKey(
        Area, models.DO_NOTHING, blank=True, null=True)
    dni = models.IntegerField(blank=True, null=True)
    nacimiento = models.DateField(blank=True, null=True)
    ingreso = models.DateTimeField(blank=True, null=True)
    puesto = models.CharField(max_length=45, blank=True, null=True)
    tip_cuenta = models.CharField(
        choices=CUENTA, max_length=45, blank=True, null=True)
    num_cuenta = models.CharField(max_length=45, blank=True, null=True)
    foto = models.FileField(upload_to='uploads/', blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    biografia = models.TextField(null=True, blank=True)
    # La calificación del colaborador
    calificacion = models.FloatField(blank=True, null=True)
    telf_emergencia = models.CharField(max_length=15, blank=True, null=True)
    nom_emergencia = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return str(self.user.first_name) + " " + str(self.user.last_name)

    @receiver(post_save, sender=User)
    def crear_colaborador(sender, instance, created, **kwargs):
        if created:
            Colaborador.objects.create(user=instance)

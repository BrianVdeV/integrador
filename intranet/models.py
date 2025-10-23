"""Modelos de la aplicación intranet"""
from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User


class TipOt(models.Model):
    """Lista de los tipos de OT"""
    codigo = models.CharField(max_length=10)
    nom_tipo = models.CharField(max_length=255, blank=True, null=True)
    cuotas = models.IntegerField(blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=100)
    observaciones = models.TextField(blank=True, null=True)
    dias1 = models.IntegerField(blank=True, null=True)
    dias2 = models.IntegerField(blank=True, null=True)
    dias3 = models.IntegerField(blank=True, null=True)
    entidad = models.CharField(blank=True, null=True, max_length=50)

    def __str__(self):
        return self.codigo


class Ot(models.Model):
    """Proyectos"""
    id_ot = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=125)
    inicio = models.DateTimeField(blank=True, null=True)
    estado = models.CharField(default='Activo', max_length=45)
    color = models.CharField(max_length=7, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    privado = models.IntegerField(default=0)
    id_tipot = models.ForeignKey(
        'TipOt', on_delete=models.CASCADE, null=True, blank=True, db_column='id_tipot')
    monto_total = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        """ Meta """
        managed = False
        db_table = 'OT'

    def __str__(self):
        return str(self.id_ot) + ' - ' + self.nombre


class Expedientes(models.Model):
    """Seguimiento de Expedientes"""
    ENTIDAD = [
        ('Enel', 'Enel'),
        ('Municipal', 'Municipal'),
        ('Notarial', 'Notarial'),
        ('Sedapal', 'Sedapal'),
        ('Sunarp', 'Sunarp'),
        ('Privado', 'Privado'),
    ]
    ot = models.ForeignKey(Ot, models.DO_NOTHING, blank=True, null=True)
    entidad = models.CharField(
        max_length=45, choices=ENTIDAD, blank=True, null=True)
    numero = models.CharField(max_length=11, blank=True, null=True)
    estado = models.CharField(max_length=45, blank=True, null=True)
    presentacion = models.DateField(blank=True, null=True)
    reingreso = models.DateField(blank=True, null=True)
    vencimiento = models.DateField(blank=True, null=True)

    class Meta:
        """ Meta """
        managed = False
        db_table = 'expedientes'

    def __str__(self):
        presentacion_year = self.presentacion.strftime(
            "%Y") if self.presentacion is not None else "Sin fecha"
        return str(presentacion_year) + ' - ' + str(self.numero)

    ESTADOS = {
        "En proceso": "#b4b4b4",
        "Presentado": "#00a7a4",
        "Reingresado": "#1d58b4",
        "Apelado": "#ef8e00",
        "En calificación": "#5a2071",
        "Inscrito": "#89be21",
        "Reservado": "#575756",
        "Distribuido": "#f31c53",
        "Liquidado": "#006633",
        "Prorrogado": "#80d0ff",
        "Observado": "red",
        "Suspendido": "#981622",
        "Tachado": "black",
        "Res. Tribunal": "black",
        "Res. Procedente": "#006633",
        "Res. Improcedente": "black",
        "Anotado": "#7eb3d5",
        "Finalizado": "#89be21",
        "Entregado al Cliente": "#89be21",
    }

    @classmethod
    def get_color(cls, estado):
        """Color asociado a un estado"""
        return cls.ESTADOS.get(estado, "#FFFFFF")  # Color por defecto: blanco

    @classmethod
    def get_choices(cls):
        """Estados de un expediente"""
        return [(key, key) for key in cls.ESTADOS.keys()]


class Eventos(models.Model):
    """Eventos"""
    titulo = models.CharField(max_length=255)
    inicio = models.DateTimeField()
    fin = models.DateTimeField(blank=True, null=True)
    ot = models.ForeignKey(Ot, on_delete=models.CASCADE, blank=True, null=True)
    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True)
    allday = models.BooleanField(default=True)
    tipo = models.CharField(max_length=255, blank=True, null=True)
    descripcion_evento = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.ot} - {self.inicio}"


class Access(models.Model):
    """Aceso a las paginas"""
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)
    url = models.CharField(max_length=500)
    timestamp = models.DateTimeField(default=now)

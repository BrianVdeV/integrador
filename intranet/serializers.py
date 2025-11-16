""" Serializers para las clases de la aplicación intranet """
import datetime
from rest_framework import serializers
from rest_framework.fields import DateField
from kanban.models import Tarea
from .models import Expedientes, Ot, TipOt, Eventos


class ExpedientesSerializer(serializers.ModelSerializer):
    """ Serializer para la clase Expedientes """
    ot_str = serializers.SerializerMethodField()

    class Meta:
        """ Meta clase para el serializer """
        model = Expedientes
        fields = '__all__'

    def get_ot_str(self, obj):
        """ Método para obtener el id en formato string """
        return str(obj.ot)


class ExpedientesListSerializer(serializers.ModelSerializer):
    """Serializers para lista de actividades"""
    titulo = serializers.SerializerMethodField()
    reingreso = DateField(format="%d/%m/%y", required=False, allow_null=True)
    vencimiento = DateField(format="%d/%m/%y", required=False, allow_null=True)

    class Meta:
        """Meta"""
        model = Expedientes
        fields = ['titulo', 'estado', 'reingreso', 'vencimiento']

    def get_titulo(self, obj):
        """Devuelve la representación en cadena del expediente."""
        return str(obj)


class OtSerializer(serializers.ModelSerializer):
    """Serializer para la clase OT"""
    id_ot_str = serializers.SerializerMethodField()

    class Meta:
        """ Meta clase para el serializer """
        model = Ot
        fields = '__all__'

    def get_id_ot_str(self, obj):
        """ Método para obtener el id_ot en formato string """
        return str(obj.id)+" - "+obj.nombre


class OtDataSerializer(serializers.ModelSerializer):
    """Serializer para la clase OT"""
    id_ot_str = serializers.SerializerMethodField()
    expediente_titles = serializers.SerializerMethodField()
    expediente_estado = serializers.SerializerMethodField()
    total_horas_proyecto = serializers.SerializerMethodField()

    # --- 1. AÑADIR NUEVO CAMPO ---
    avance = serializers.SerializerMethodField()

    class Meta:
        model = Ot
        fields = [
            'id',
            'id_ot_str',
            'color',
            'inicio',
            'estado',
            'expediente_titles',
            'expediente_estado',
            'privado',
            'total_horas_proyecto',
            'avance',  # --- 2. INCLUIR CAMPO EN LA LISTA ---
        ]

    # --- 3. AÑADIR MÉTODO PARA CALCULAR EL AVANCE ---
    def get_avance(self, obj):
        """
        Calcula el porcentaje de tareas completadas para una OT.
        """
        total_tareas = Tarea.objects.filter(ot=obj).count()
        if total_tareas == 0:
            return 0

        tareas_completadas = Tarea.objects.filter(
            ot=obj, estado='done').count()
        porcentaje = round((tareas_completadas / total_tareas) * 100)
        return porcentaje

    def get_id_ot_str(self, obj):
        return f"{obj.id} - {obj.nombre}"

    def get_expediente_titles(self, obj):
        expediente = Expedientes.objects.filter(ot=obj).first()
        if expediente:
            presentacion = expediente.presentacion
            if isinstance(presentacion, datetime.date):
                año = presentacion.year
            else:
                año = "Sin Fecha"
            return f"{año}- {expediente.numero}"
        return None

    def get_expediente_estado(self, obj):
        expediente = Expedientes.objects.filter(ot=obj).first()
        if expediente:
            return expediente.estado
        return None

    def get_total_horas_proyecto(self, obj):
        total_segundos = 0
        for actividad in obj.actividades_set.all():
            if actividad.fin and actividad.inicio:
                total_segundos += (actividad.fin -
                                   actividad.inicio).total_seconds()
        horas = int(total_segundos // 3600)
        minutos = int((total_segundos % 3600) // 60)
        return f"{horas:02d}:{minutos:02d}"


class FeriadoSerializer(serializers.Serializer):
    fecha = serializers.DateField()
    nombre = serializers.CharField(max_length=255)


class TipOtSerializer(serializers.ModelSerializer):
    """Serializer para la clase Tipo OT"""
    class Meta:
        """ Meta clase para el serializer """
        model = TipOt
        fields = '__all__'


class EventosSerializer(serializers.ModelSerializer):
    """Serializer para los eventos del calendario"""
    class Meta:
        """Meta clase para el serializer """
        model = Eventos
        fields = '__all__'


class CalendarioSerializer(serializers.Serializer):
    """Serializer para el calendario"""
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=255)
    start = serializers.CharField()
    end = serializers.CharField(required=False, allow_blank=True)
    ot = serializers.CharField(required=False, allow_blank=True)
    usuario = serializers.CharField(required=False, allow_blank=True)
    descripcion = serializers.CharField()
    allDay = serializers.BooleanField()
    className = serializers.CharField()


class NotificacionesSerializers(serializers.Serializer):
    """Serializer para las notificaciones"""
    id = serializers.IntegerField()
    titulo = serializers.CharField(max_length=255)
    descripcion = serializers.CharField(max_length=500)
    fecha = serializers.DateTimeField()
    tipo = serializers.CharField(max_length=50)


class SidebarSerializer(serializers.Serializer):
    """Badges para sidebar"""
    agenda = serializers.IntegerField()

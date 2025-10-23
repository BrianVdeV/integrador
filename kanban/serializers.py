"""Serializer for Tarea model."""
from datetime import timedelta, datetime
from django.db.models import Sum, F, ExpressionWrapper, DurationField
from rest_framework import serializers
from rest_framework.fields import DateTimeField
from intranet.serializers import ExpedientesListSerializer
from .models import Tarea, Actividades


class TareaSerializer(serializers.ModelSerializer):
    """Serializer for Tarea model."""
    user_name = serializers.SerializerMethodField()
    ot_str = serializers.CharField(source="ot", read_only=True)
    duracion = serializers.SerializerMethodField()
    duracion_input = serializers.CharField(write_only=True, required=False)
    horas_trabajadas = serializers.SerializerMethodField()
    participantes = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = Tarea
        fields = ['id', 'ot', 'ot_str', 'titulo', 'descripcion',
                  'estado', 'creado', 'user', 'user_name', 'prioridad', 'vencimiento',
                  'duracion', 'duracion_input', 'orden', 'participantes', 'horas_trabajadas']
        read_only_fields = ['user_name', 'ot_str']

    def get_user_name(self, obj):
        """Mostrar nombre de usuario."""
        return obj.user.username if obj.user else None

    def get_duracion(self, obj):
        """ Devuelve solo HH:MM"""
        if obj.duracion:
            total_seconds = int(obj.duracion.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours:02}:{minutes:02}"
        return None

    def get_horas_trabajadas(self, obj):
        """Suma de todas las horas trabajadas en actividades de la tarea"""

        # Creamos un campo calculado fin - inicio
        qs = Actividades.objects.filter(tarea=obj, fin__isnull=False)
        qs = qs.annotate(duracion=ExpressionWrapper(
            F("fin") - F("inicio"), output_field=DurationField()
        ))

        total = qs.aggregate(total=Sum("duracion"))["total"]

        if total:
            horas = total.total_seconds() // 3600
            minutos = (total.total_seconds() % 3600) // 60
            return f"{int(horas):02}:{int(minutos):02}"
        return "00:00"

    def get_participantes(self, obj):
        """Usuarios que participaron en actividades de la tarea"""
        from .models import Actividades

        users = (
            Actividades.objects.filter(tarea=obj, user__isnull=False)
            .values_list("user__username", flat=True)
            .distinct()
        )
        return list(users)

    def validate(self, data):
        duracion_str = data.pop("duracion_input", None)
        if duracion_str:
            try:
                hours, minutes = map(int, duracion_str.split(":"))
                data["duracion"] = timedelta(hours=hours, minutes=minutes)
            except ValueError:
                raise serializers.ValidationError(
                    "Formato de duración inválido. Usa hh:mm.")
        return data


class ActividadesSerializer(serializers.ModelSerializer):
    """ Serializer principal para CRUD de Actividades """
    class Meta:
        model = Actividades
        fields = '__all__'


class InformesSerializer(serializers.ModelSerializer):
    """Muestra los informes"""
    user = serializers.StringRelatedField()
    ot = serializers.StringRelatedField()
    tarea = serializers.StringRelatedField()
    comentario = serializers.SerializerMethodField()
    expedientes = ExpedientesListSerializer(
        many=True, read_only=True, source='ot.expedientes_set')
    total = serializers.SerializerMethodField()
    total_decimal = serializers.SerializerMethodField()
    inicio = DateTimeField(format="%H:%M")  # Formato de 24 horas (HH:MM)
    fin = DateTimeField(format="%H:%M", allow_null=True)
    fecha = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = Actividades
        fields = ['id', 'user', 'ot', 'tarea', 'comentario',
                  'inicio', 'fin', 'fecha', 'expedientes', 'total', 'total_decimal']

    def get_comentario(self, obj):
        """Devuelve el comentario en minúsculas."""
        if obj.comentario:
            return obj.comentario.lower()
        return None

    def get_fecha(self, obj):
        """Extrae y formatea la fecha del campo 'inicio' a dd/mm/yy."""
        if obj.inicio:
            # obj.inicio es un datetime.datetime. Utilizamos strftime para formatear.
            return obj.inicio.strftime("%d/%m/%y")
        return None

    def get_total(self, obj):
        """Muestra el total de horas trabajadas en la actividad"""
        return obj.total()

    def get_total_decimal(self, obj):
        """Muestra el total en decimal de horas trabajadas en la actividad"""
        return obj.total_decimal()


class ActividadesDashboardSerializer(serializers.ModelSerializer):
    """Serializer específico para el dashboard - Solo lectura con formato"""
    user = serializers.SerializerMethodField()
    tarea = serializers.SerializerMethodField()
    tarea_completa = serializers.SerializerMethodField()
    ot = serializers.SerializerMethodField()
    ot_completa = serializers.SerializerMethodField()
    inicio = serializers.SerializerMethodField()
    comentario = serializers.SerializerMethodField()
    comentario_completo = serializers.SerializerMethodField()
    en_actividad = serializers.SerializerMethodField()
    tiempo_actividad = serializers.SerializerMethodField()
    inicio_completo = serializers.SerializerMethodField()
    fecha_actividad = serializers.SerializerMethodField()

    class Meta:
        model = Actividades
        fields = ['id', 'user', 'tarea', 'tarea_completa', 'ot', 'ot_completa',
                  'inicio', 'inicio_completo', 'comentario', 'comentario_completo',
                  'en_actividad', 'tiempo_actividad', 'fecha_actividad']

    def get_user(self, obj):
        # SOLO username, sin nombre completo
        return obj.user.username

    def get_tarea(self, obj):
        """Versión corta para mostrar en la tabla"""
        return f"<strong>{obj.tarea.titulo if obj.tarea else 'Sin tarea'}</strong><br>"

    def get_tarea_completa(self, obj):
        """Versión completa para el tooltip"""
        if obj.tarea:
            return f"{obj.tarea.titulo}"
        return "Sin tarea"

    def get_ot(self, obj):
        """Versión con número Y nombre de la OT"""
        if obj.ot:
            return f"{obj.ot.id_ot} - {obj.ot.nombre}"
        return "Sin OT"

    def get_ot_completa(self, obj):
        """Versión completa para el tooltip"""
        if obj.ot:
            return f"{obj.ot.id_ot} - {obj.ot.nombre}"
        return "Sin OT"

    def get_inicio(self, obj):
        return obj.inicio.strftime('%H:%M:%S') if obj.inicio else '-'

    def get_comentario(self, obj):
        """Versión corta (50 caracteres) para la tabla"""
        if len(obj.comentario) > 50:
            return obj.comentario[:50] + "..."
        return obj.comentario

    def get_comentario_completo(self, obj):
        """Versión completa para el tooltip"""
        return obj.comentario

    def get_en_actividad(self, obj):
        """Verifica si el usuario tiene una actividad activa (sin fin)"""
        return obj.fin is None

    def get_inicio_completo(self, obj):
        """Devuelve la fecha/hora completa para el cronómetro"""
        return obj.inicio.isoformat() if obj.inicio else None

    def get_fecha_actividad(self, obj):
        """
        Si está en actividad: retorna la fecha de HOY
        Si ya finalizó: retorna la fecha de término
        """
        from django.utils import timezone
        if obj.fin is None:
            return timezone.now().strftime('%Y-%m-%d')
        else:
            return obj.fin.strftime('%Y-%m-%d') if obj.fin else '-'

    def get_tiempo_actividad(self, obj):
        """
        Si está en actividad (fin=None): retorna None para que el frontend calcule en tiempo real
        Si ya finalizó: calcula y retorna el tiempo total que duró
        """
        if obj.fin is None:
            return None
        else:
            if obj.inicio and obj.fin:
                diferencia = obj.fin - obj.inicio
                total_segundos = int(diferencia.total_seconds())
                horas = total_segundos // 3600
                minutos = (total_segundos % 3600) // 60
                segundos = total_segundos % 60
                return f"{horas:02d}:{minutos:02d}:{segundos:02d}"
            return "00:00:00"
    """Serializer específico para el dashboard - Solo lectura con formato"""
    user = serializers.SerializerMethodField()
    tarea = serializers.SerializerMethodField()
    tarea_completa = serializers.SerializerMethodField()
    ot = serializers.SerializerMethodField()
    ot_completa = serializers.SerializerMethodField()
    inicio = serializers.SerializerMethodField()
    comentario = serializers.SerializerMethodField()
    comentario_completo = serializers.SerializerMethodField()
    en_actividad = serializers.SerializerMethodField()
    tiempo_actividad = serializers.SerializerMethodField()
    inicio_completo = serializers.SerializerMethodField()
    fecha_actividad = serializers.SerializerMethodField()

    class Meta:
        model = Actividades
        fields = ['id', 'user', 'tarea', 'tarea_completa', 'ot', 'ot_completa',
                  'inicio', 'inicio_completo', 'comentario', 'comentario_completo',
                  'en_actividad', 'tiempo_actividad', 'fecha_actividad']

    def get_user(self, obj):
        return obj.user.username

    def get_tarea(self, obj):
        """Versión corta para mostrar en la tabla"""
        return f"<strong>{obj.tarea.titulo if obj.tarea else 'Sin tarea'}</strong><br>"

    def get_tarea_completa(self, obj):
        """Versión completa para el tooltip"""
        if obj.tarea:
            return f"{obj.tarea.titulo}"
        return "Sin tarea"

    def get_ot(self, obj):
        """Versión con número Y nombre de la OT"""
        if obj.ot:
            # Usando el campo 'nombre' que viste en la imagen
            return f"{obj.ot.id_ot} - {obj.ot.nombre}"
        return "Sin OT"

    def get_ot_completa(self, obj):
        """Versión completa para el tooltip"""
        if obj.ot:
            return f"{obj.ot.id_ot} - {obj.ot.nombre}"
        return "Sin OT"

    def get_inicio(self, obj):
        return obj.inicio.strftime('%H:%M:%S') if obj.inicio else '-'

    def get_comentario(self, obj):
        """Versión corta (50 caracteres) para la tabla"""
        if len(obj.comentario) > 50:
            return obj.comentario[:50] + "..."
        return obj.comentario

    def get_comentario_completo(self, obj):
        """Versión completa para el tooltip"""
        return obj.comentario

    def get_en_actividad(self, obj):
        """Verifica si el usuario tiene una actividad activa (sin fin)"""
        return obj.fin is None

    def get_inicio_completo(self, obj):
        """Devuelve la fecha/hora completa para el cronómetro"""
        return obj.inicio.isoformat() if obj.inicio else None

    def get_fecha_actividad(self, obj):
        """
        Si está en actividad: retorna la fecha de HOY
        Si ya finalizó: retorna la fecha de término
        """
        from django.utils import timezone
        if obj.fin is None:
            # Actividad en curso - fecha de hoy
            return timezone.now().strftime('%Y-%m-%d')
        else:
            # Actividad finalizada - fecha de término
            return obj.fin.strftime('%Y-%m-%d') if obj.fin else '-'

    def get_tiempo_actividad(self, obj):
        """
        Si está en actividad (fin=None): retorna None para que el frontend calcule en tiempo real
        Si ya finalizó: calcula y retorna el tiempo total que duró
        """
        if obj.fin is None:
            # Actividad en curso - el frontend mostrará cronómetro
            return None
        else:
            # Actividad finalizada - calculamos el tiempo total
            if obj.inicio and obj.fin:
                diferencia = obj.fin - obj.inicio
                total_segundos = int(diferencia.total_seconds())
                horas = total_segundos // 3600
                minutos = (total_segundos % 3600) // 60
                segundos = total_segundos % 60
                return f"{horas:02d}:{minutos:02d}:{segundos:02d}"
            return "00:00:00"

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Area, Colaborador


class UserSerializer(serializers.ModelSerializer):
    """Serializer"""
    colaborador = serializers.SerializerMethodField()
    # Nuevo campo para la fecha de nacimiento
    nacimiento = serializers.SerializerMethodField()

    class Meta:
        """Meta"""
        model = User
        fields = ['username', 'email', 'first_name',
                  'last_name', 'colaborador', 'nacimiento']

    def get_colaborador(self, obj):
        try:
            colaborador = Colaborador.objects.get(user=obj)
            # Serializar los datos de Colaborador
            return ColaboradorSerializer(colaborador).data
        except Colaborador.DoesNotExist:
            return None  # Si el usuario no tiene colaborador, devolver None

    def get_nacimiento(self, obj):
        try:
            colaborador = Colaborador.objects.get(user=obj)
            if colaborador.nacimiento:  # Verifica si la fecha de nacimiento no es None
                # Formato legible
                return colaborador.nacimiento.strftime('%Y-%m-%d')
            return None  # Si la fecha de nacimiento es None, devuelve None
        except Colaborador.DoesNotExist:
            return None


class Select2Serializer(serializers.Serializer):
    """Serializer para los select2"""
    id = serializers.IntegerField()
    text = serializers.CharField(max_length=255)

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'text': str(instance)
        }


class ColaboradorSerializer(serializers.ModelSerializer):
    """Serializer"""
    class Meta:
        """Meta"""
        model = Colaborador
        fields = '__all__'


class AreaSerializer(serializers.ModelSerializer):
    """Serializer"""
    class Meta:
        """Meta"""
        model = Area
        fields = ['id', 'nombre', 'codigo']

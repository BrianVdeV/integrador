"""Vista de admin"""
from django.contrib import admin
from .models import Ot, Expedientes, TipOt, Eventos

# Register your models here.


@admin.register(Ot)
class OtAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'estado')
    search_fields = ('id', 'nombre', 'estado')
    list_filter = ('estado',)


@admin.register(Expedientes)
class ExpedientesAdmin(admin.ModelAdmin):
    list_display = ('id', 'ot', 'estado', 'numero',
                    'presentacion', 'reingreso', 'vencimiento')
    search_fields = ('ot__id', 'estado', 'numero')
    list_filter = ('estado',)


admin.site.register(TipOt)
admin.site.register(Eventos)

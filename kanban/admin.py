from django.contrib import admin
from .models import Tarea, Actividades


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    """Admin para Tareas"""
    list_display = ['id', 'titulo', 'user', 'ot', 'estado',
                    'vencimiento', 'creado']
    list_filter = ['estado', 'user', 'creado']
    search_fields = ['titulo', 'descripcion', 'ot__id', 'user__username']
    readonly_fields = ['creado', 'editado']
    list_editable = ['estado']
    fieldsets = (
        ('Información Principal', {
            'fields': ('titulo', 'descripcion', 'user', 'ot')
        }),
        ('Detalles de la Tarea', {
            'fields': ('estado', 'prioridad', 'vencimiento', 'duracion', 'orden')
        }),
        ('Fechas', {
            'fields': ('creado', 'editado'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Actividades)
class ActividadesAdmin(admin.ModelAdmin):
    """Admin para Actividades"""
    list_display = ['id', 'user', 'inicio', 'fin', 'ot', 'tarea']
    list_filter = ['inicio', 'fin', 'user']
    search_fields = ['comentario', 'user__username',
                     'tarea__titulo', 'ot__id']

    fieldsets = (
        ('Detalles', {
            'fields': ('user', 'ot', 'tarea', 'comentario')
        }),
        ('Tiempo', {
            'fields': ('inicio', 'fin')
        })
    )

"""URL"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'tarea', views.TareaViewSet, 'tarea')
router.register(r'kanban', views.KanbanViewSet, 'kanban')
router.register(r'actividades', views.ActividadesViewSet, 'actividades')
router.register(r'informes', views.InformesViewSet, 'informes')
urlpatterns = [
    path('api/', include(router.urls)),
    path('kanban/', views.tarea_kanban_view, name="tarea_kanban"),
    path('kanban_tarea/', views.tarea_lista_view,
         name='tarea_lista'),
    path('add_tarea/', views.add_tarea, name='add_tarea'),
]

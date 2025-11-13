"""URL"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from intranet import views, api

router = routers.DefaultRouter()
router.register(r'ot', api.OtViewSet, 'ot')
router.register(r'ot-activo', api.OtActivoViewSet, 'ot-activo')
router.register(r'expedientes', api.ExpedientesViewSet, 'expedientes')
router.register(r'tipot', api.TipOtViewSet)
router.register(r'eventos', api.EventosViewSet, 'eventos')


urlpatterns = [
    path('api/', include(router.urls)),
    path('api/csrf/', views.csrf_token_view),
    path('api/chart/',
         api.ChartView.as_view(), name='chart'),
    path('api/calendario/', api.CalendarioView.as_view(), name='calendario-list'),
    path('', views.index, name='index'),
    path('api/ots/', api.OTListAPIView.as_view(), name='api_ots'),
    path('api/notificaciones/', api.NotificacionesView.as_view(),
         name='notificaciones'),
    path('actividades/api/', views.end_actividad,
         name='end_actividad'),
    path('calendario/', views.calendario, name='calendario'),
    path('resumen/', views.resumen, name='resumen'),
    path('exportar_actividades_excel/', views.export_actividades_excel,
         name='exportar_actividades_excel'),
    path('exportar_resumen_excel/', views.export_resumen_excel,
         name='exportar_resumen_excel'),
    path('dashboard/proyectos', views.dashboard, name='dashboard_proyectos'),
    path('detallado/', views.detallado, name='detallado'),
    path('proyectos/', views.proyectos, name='proyectos'),
    path('proyectos/edit/<int:id_ot>/',
         views.edit_proyecto, name='edit_proyecto'),
    path('proyectos/delete', views.delete_proyecto, name='delete_proyecto'),
    path('proyectos/<int:id_ot>/', views.proyecto_detalle,
         name='proyecto_detalle'),
    path('expedientes/', views.expedientes, name='expedientes'),
    path('obtener-notificaciones/', views.obtener_notificaciones,
         name='obtener_notificaciones'),
    path('sidebar', api.SidebarView.as_view(), name="sidebar"),
    path('index/api/', views.list_actividades_index,
         name='obtener_actividades_index'),  # NUEVA RUTA
    path('', views.index, name='index'),
    path('api/reportes-pdf/', views.ReportePDFView.as_view(), name='reportes_pdf'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

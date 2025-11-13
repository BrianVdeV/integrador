"""Clases usando DRF"""
from datetime import datetime
import os
import json
import uuid
from collections import defaultdict
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.contrib.auth.models import User
from django.utils.timezone import timedelta, now
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView
from rest_framework.decorators import action
from auth.models import Colaborador
from kanban.models import Tarea, Actividades
from kanban.serializers import ActividadesSerializer
from .serializers import (ExpedientesSerializer, OtSerializer,
                          OtDataSerializer, TipOtSerializer,
                          CalendarioSerializer, EventosSerializer, SidebarSerializer)
from .models import Expedientes, Ot, TipOt, Eventos, Access


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'page_size'
    max_page_size = 10000


class ExpedientesViewSet(viewsets.ModelViewSet):
    """ViewSet para los expedientes"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ExpedientesSerializer
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        """
        Sobrescribe el queryset para aplicar el filtro de estado de OT.
        """
        queryset = Expedientes.objects.select_related(
            'ot').all().order_by('-ot')
        ot_estado = self.request.query_params.get('ot_estado', None)
        if ot_estado:
            queryset = queryset.filter(ot__estado=ot_estado)
        return queryset


class OtViewSet(viewsets.ModelViewSet):
    """Lista todas las ot"""
    queryset = Ot.objects.all().order_by('-id_ot')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OtSerializer
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(id_ot__icontains=search)
        return queryset


class OtActivoViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OtSerializer
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        if self.request.user.is_superuser:
            ots = Ot.objects.filter(estado="Activo").order_by('-id_ot')
            return ots
        return ots.filter(privado=0)


class OTListAPIView(ListAPIView):
    serializer_class = OtDataSerializer
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        return Ot.objects.all().order_by('-id_ot')

    def list(self, request, *args, **kwargs):
        """Modifica la respuesta para que sea compatible con DataTables"""
        draw = int(request.GET.get("draw", 1))
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 50))
        search_value = request.GET.get("search[value]", "").strip()

        queryset = self.get_queryset()

        if search_value:
            queryset = queryset.filter(
                Q(nombre__icontains=search_value) |
                Q(id_ot__icontains=search_value)
            )

        total_count = queryset.count()
        paginator = Paginator(queryset, length)
        page_number = (start // length) + 1
        page = paginator.get_page(page_number)
        serializer = self.get_serializer(page, many=True)

        return Response({
            "draw": draw,
            "recordsTotal": total_count,
            "recordsFiltered": total_count,
            "data": serializer.data,
        })


class ChartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search = request.GET.get('search[value]', '').strip()
        start_date = request.GET.get('start_date', '2025-03-02')
        end_date = request.GET.get('end_date', '2025-03-08')

        try:
            start_range = datetime.strptime(start_date, "%Y-%m-%d")
            end_range = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return Response({"error": "Formato de fecha inválido"}, status=400)

        date_range = [(start_range + timedelta(days=i)).strftime("%Y-%m-%d")
                      for i in range((end_range - start_range).days + 1)]

        queryset = Actividades.objects.filter(
            fin__isnull=False,
            inicio__date__range=(start_date, end_date)
        )

        if search:
            if search.isdigit():
                queryset = queryset.filter(ot_id=search)
            else:
                try:
                    queryset = queryset.filter(
                        user__username__startswith=search)
                except Exception as e:
                    return Response({"error": f"Error al buscar usuario: {str(e)}"}, status=500)

        queryset = queryset.order_by('-ot')
        data = defaultdict(lambda: {date: 0 for date in date_range})
        data_label = defaultdict(lambda: {date: "0:00" for date in date_range})
        totals = {date: 0 for date in date_range}
        totals_label = {date: "0:00" for date in date_range}

        for actividad in queryset:
            fecha = actividad.fin.strftime("%Y-%m-%d")
            ot_label = str(actividad.ot)[
                :20] if actividad.ot else "Sin OT"
            color = actividad.ot.color if actividad.ot else "#000000"
            total_minutos = int(actividad.total_decimal() * 60)
            data[ot_label][fecha] += total_minutos
            totals[fecha] += total_minutos
            if "color" not in data[ot_label]:
                data[ot_label]["color"] = color

        for ot_label, fechas in data.items():
            for fecha in fechas:
                if fecha != "color":
                    minutos = fechas[fecha]
                    horas = minutos // 60
                    restante = minutos % 60
                    data_label[ot_label][fecha] = f"{horas}:{str(restante).zfill(2)}"

        for fecha in totals:
            minutos = totals[fecha]
            horas = minutos // 60
            restante = minutos % 60
            totals_label[fecha] = f"{horas}:{str(restante).zfill(2)}"

        datasets = [
            {
                "label": ot_label,
                "data": [data[ot_label][fecha] / 60 for fecha in date_range],
                "data_label": [data_label[ot_label][fecha] for fecha in date_range],
                "backgroundColor": data[ot_label]["color"]
            }
            for ot_label in data
        ]

        return Response({
            "labels": date_range,
            "datasets": datasets,
            "totals": [totals_label[fecha] for fecha in date_range]
        })


class TipOtViewSet(viewsets.ModelViewSet):
    """Tipo OT"""
    queryset = TipOt.objects.all()
    serializer_class = TipOtSerializer
    pagination_class = LargeResultsSetPagination

    @action(detail=False, methods=['get'])
    def incluir_todos(self, request):
        """Por ahora incluye solo 3 de SUNARP"""
        queryset = TipOt.objects.filter(id__in=[1, 2, 4])
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CalendarioView(APIView):
    """API Calendario"""

    def get(self, request):
        """Metodo GET"""
        calendario = []
        eventos = Eventos.objects.all()
        for evento in eventos:
            calendario.append({
                "id": evento.id,
                "title": evento.titulo,
                "start": evento.inicio,
                "end": evento.fin,
                "ot": evento.ot.id_ot if evento.ot else None,
                "usuario": evento.usuario.username if evento.usuario else None,
                "descripcion": evento.descripcion_evento,
                "allDay": evento.allday,
                "className": "bg-primary"
            })
        expedientes = Expedientes.objects.filter(
            (Q(reingreso__isnull=False) | Q(vencimiento__isnull=False)) &
            ~Q(estado__in=['Inscrito', 'Tachado'])
        ).order_by('-id')

        for expediente in expedientes:
            if expediente.reingreso:
                calendario.append({
                    "id": expediente.id,
                    "title": f"OT: {expediente.ot.id_ot}",
                    "start": expediente.reingreso,
                    "ot": expediente.ot,
                    "descripcion": f"Estado: {expediente.estado}",
                    "allDay": True,
                    "className": "bg-warning"
                })
            if expediente.vencimiento:
                calendario.append({
                    "id": expediente.id,
                    "title": f"OT {expediente.ot.id_ot}",
                    "start": expediente.vencimiento,
                    "ot": expediente.ot,
                    "descripcion": f"Estado: {expediente.estado}",
                    "allDay": True,
                    "className": "bg-danger"
                })

        # ========================
        # TAREAS MUY URGENTES
        # ========================
        tareas_urgentes = Tarea.objects.filter(
            prioridad='high',
            vencimiento__isnull=False
        ).select_related('ot', 'user')

        for tarea in tareas_urgentes:
            calendario.append({
                "id": tarea.id + 1000000,
                # ----------------------------------
                "title": f"⚠️ TAREA: {tarea.titulo}",
                "start": tarea.vencimiento,
                "ot": tarea.ot.id_ot if tarea.ot else None,
                "usuario": tarea.user.username if tarea.user else None,
                "descripcion": f"Prioridad: Muy Urgente. {tarea.descripcion or ''}",
                "allDay": True,
                "className": "bg-primary"
            })

        # ========================
        # CUMPLEAÑOS
        # ========================
        cumples = Colaborador.objects.filter(
            user__is_active=True)
        anio_actual = datetime.now().year
        for cumple in cumples:
            if cumple.nacimiento:
                fecha_cumple = datetime(
                    anio_actual, cumple.nacimiento.month, cumple.nacimiento.day)
                calendario.append({
                    "id": cumple.id,
                    "title": f"🎂 {cumple.user}",
                    "start": fecha_cumple.strftime("%Y-%m-%d"),
                    "usuario": cumple.user.username,
                    "descripcion": f"Cumpleaños de {cumple.user}",
                    "allDay": True,
                    "className": "bg-info"
                })
        feriados_path = os.path.join(
            settings.BASE_DIR, 'static', 'docs', 'feriados.json')
        if os.path.exists(feriados_path):
            with open(feriados_path, encoding='utf-8') as f:
                feriados = json.load(f)
                for feriado in feriados:
                    date = feriado.get("date")
                    name = feriado.get("name")
                    if date:
                        calendario.append({
                            # Este "1" funciona porque int("1") es válido.
                            "id": "1",
                            "title": f"🌞 {name}",
                            "start": date,
                            "descripcion": name,
                            "allDay": True,
                            "className": "bg-secondary"
                        })
        serializer = CalendarioSerializer(calendario, many=True)
        return Response(serializer.data)


class NotificacionesView(APIView):
    """API para notificaciones en los próximos 7 días"""

    def get(self, request):
        hoy = datetime.now().date()
        fin = hoy + timedelta(days=7)

        # Obtener eventos desde el CalendarioView
        base_view = CalendarioView()
        response = base_view.get(request)
        eventos = response.data

        proximos = []
        for evento in eventos:
            start_str = evento.get('start')
            end_str = evento.get('end')
            className = evento.get('className', '')

            # Intentar parsear start
            try:
                start_dt = datetime.fromisoformat(start_str)
            except Exception:
                continue

            # Filtrar rango de fechas (solo día)
            if not (hoy <= start_dt.date() <= fin):
                continue

            # Filtrar eventos bg-primary que ya pasaron (hora actual > end)
            if className == "bg-primary" and end_str:
                try:
                    end_dt = datetime.fromisoformat(end_str)
                    if now() > end_dt:
                        continue  # ya terminó el evento, no mostrar
                except Exception:
                    pass  # si no puede convertir, lo dejamos pasar por ahora

            # Personalizar contenido
            if className == "bg-primary":
                hora = start_dt.strftime("%H:%M")
                titulo = evento.get('title', 'Nuevo Evento')
                mensaje = f"{hora} {titulo} asignado a {evento.get('usuario', '')}"
            elif className == "bg-info":
                titulo = f"¡Feliz Cumpleaños {evento.get('usuario', '')}!"
                mensaje = f"Se acerca el cumpleaños de {evento.get('usuario', '')}. ¡Te deseamos un feliz cumpleaños!"
            elif className == "bg-warning":
                titulo = evento.get('ot', 'Expediente de SUNARP')
                mensaje = "Expediente de SUNARP por max. reingreso."
            elif className == "bg-danger":
                titulo = evento.get('ot')
                mensaje = "Expediente de SUNARP próximo a vencer."
            elif className == "bg-success":
                titulo = f"🌴 ¡Vacaciones de  {evento.get('usuario', '')}!"
                start_fmt = datetime.fromisoformat(start_str).strftime("%d/%m")
                end_fmt = datetime.fromisoformat(end_str).strftime("%d/%m")
                mensaje = f"Vacaciones de {evento.get('usuario', '')} del {start_fmt} al {end_fmt}."
            else:
                titulo = evento.get('title', 'Nuevo Evento')
                mensaje = "Tienes un nuevo evento."

            evento["titulo"] = titulo
            evento["mensaje"] = mensaje

            proximos.append(evento)

        # Ordenar por fecha de inicio
        proximos.sort(key=lambda x: x['start'])

        return Response(proximos)


class EventosViewSet(viewsets.ModelViewSet):
    """ViewSet para los eventos"""
    queryset = Eventos.objects.order_by('id')
    serializer_class = EventosSerializer
    permission_classes = [permissions.IsAuthenticated]


class SidebarView(APIView):
    """Vista badges sidebar"""
    serializer_class = SidebarSerializer

    def get(self, request, format=None):
        user = request.user
        access = Access.objects.filter(
            user=user).order_by("-timestamp").first()
        if user.is_superuser:
            agenda_count = Tarea.objects.filter(
                editado__gt=access.timestamp).count()
        elif access:
            agenda_count = Tarea.objects.filter(
                editado__gt=access.timestamp, user=user).count()
        else:
            agenda_count = Tarea.objects.count()

        data = {
            "agenda": agenda_count
        }

        serializer = SidebarSerializer(data)
        return Response(serializer.data)

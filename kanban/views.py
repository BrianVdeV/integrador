"""Kanban"""
from datetime import date, datetime, timedelta
from django.conf import settings
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.db.models import OuterRef, Subquery, Q
from django.utils import timezone
from django.utils.timezone import now
from django_filters import CharFilter, FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from intranet.models import Ot, Access
from .models import Tarea, Actividades
from .serializers import TareaSerializer, ActividadesSerializer, ActividadesDashboardSerializer, InformesSerializer
from .forms import TareaForm
# Create your views here.


def tarea_kanban_view(request):
    """Template kanban"""
    form = TareaForm()

    access, created = Access.objects.get_or_create(
        user=request.user,
        url=request.path,
    )
    access.timestamp = now()
    access.save()

    context = {
        "form": form
    }
    return render(request, "kanban.html", context)


def tarea_lista_view(request):
    """Vista para mostrar la lista de tareas"""
    form = TareaForm()

    # Obtener todos los usuarios activos para el filtro
    users = User.objects.filter(is_active=True)

    context = {
        "form": form,
        "users": users  # Pasar los usuarios al contexto
    }
    return render(request, 'kanban_tarea.html', context)


class TareaFilter(FilterSet):
    """Definimos un nuevo campo de filtro llamado 'vencimiento_rango'"""
    vencimiento_rango = CharFilter(method='filter_vencimiento_rango')
    today = date.today()

    class Meta:
        """Meta"""
        model = Tarea
        fields = ['ot', 'user', 'vencimiento']

    def filter_vencimiento_rango(self, queryset, name, value):
        """El 'value' será el texto enviado desde el frontend (ej: 'today', 'past7days')"""
        if value == 'today':
            return queryset.filter(vencimiento=self.today)
        elif value == 'pastweek':
            seven_days_ago = self.today - timedelta(days=7)
            return queryset.filter(vencimiento__date__range=[seven_days_ago, self.today])
        elif value == 'thisweek':
            start_of_week = self.today - timedelta(days=self.today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            return queryset.filter(vencimiento__date__range=[start_of_week, end_of_week])
        elif value == 'thismonth':
            return queryset.filter(
                vencimiento__year=self.today.year, vencimiento__month=self.today.month)
        elif value == 'thisyear':
            return queryset.filter(vencimiento__year=self.today.year)
        return queryset


class TareaViewSet(viewsets.ModelViewSet):
    """API Tarea"""
    queryset = Tarea.objects.all()
    serializer_class = TareaSerializer
    # Asegura que solo usuarios autenticados accedan
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = TareaFilter
    filterset_fields = ['ot', 'user']
    ordering_fields = ['titulo']

    @action(detail=False, methods=['get'])
    def datatables(self, request):
        """Modifica la respuesta para que sea compatible con DataTables"""

        draw = int(request.GET.get("draw", 1))
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 10))
        # El 'search_value' ahora viene de d.search, no de search[value]
        search_value = request.GET.get("search", "").strip()

        # Obtenemos el queryset base
        queryset = self.get_queryset()

        # Total de registros SIN filtrar
        records_total = queryset.count()

        # --- FILTROS ---
        # Obtenemos los parámetros de los filtros personalizados
        estado = request.GET.get('estado')
        responsable_id = request.GET.get('responsable')
        rango_vencimiento = request.GET.get('vencimiento')
        duracion_filter = request.GET.get('duracion')

        # Filtro de búsqueda general
        if search_value:
            queryset = queryset.filter(
                Q(titulo__icontains=search_value) |
                Q(descripcion__icontains=search_value) |
                Q(ot__id_ot__icontains=search_value) |
                Q(user__username__icontains=search_value)
            )

        # Aplicar los filtros de los select/input
        if estado:
            queryset = queryset.filter(estado=estado)

        if responsable_id:
            queryset = queryset.filter(user_id=responsable_id)

        if rango_vencimiento and ' to ' in rango_vencimiento:
            try:
                start_date, end_date = rango_vencimiento.split(' to ')
                queryset = queryset.filter(vencimiento__date__range=[
                    start_date, end_date])
            except ValueError:
                pass

        # Filtro por duración (tiempo estimado)
        if duracion_filter:
            try:
                # Asumimos formato HH:MM
                h, m = map(int, duracion_filter.split(':'))
                td = timedelta(hours=h, minutes=m)
                # Filtramos por la duración exacta
                queryset = queryset.filter(duracion=td)
            except (ValueError, TypeError):
                # Si el formato es incorrecto (ej: "1:"), no filtra
                pass

        # --- ORDENAMIENTO (SECCIÓN CORREGIDA) ---

        # 1. Intentar obtener el orden de DataTables (clic en flechas)
        order_column_index = request.GET.get('order[0][column]')
        order_dir = request.GET.get('order[0][dir]', 'asc')

        # 2. Obtener el orden del dropdown personalizado
        custom_ordering = request.GET.get('ordering')

        # Mapeo de índice de columna a campo del modelo
        # Debe coincidir con el orden en 'columns' de JavaScript
        column_field_map = [
            'estado',           # 0
            'ot__id_ot',        # 1 (Ordenamos por el ID de la OT)
            'titulo',           # 2
            'vencimiento',      # 3
            'duracion',         # 4
            'user__username',   # 5 (Ordenamos por el nombre de usuario)
            None                # 6 (Acciones, no ordenable)
        ]

        order_field = None

        if order_column_index is not None:
            try:
                col_index = int(order_column_index)
                field_name = column_field_map[col_index]

                if field_name:
                    prefix = '-' if order_dir == 'desc' else ''
                    order_field = f"{prefix}{field_name}"
            except (IndexError, ValueError):
                pass  # Índice de columna inválido, se ignora

        # 3. Si DataTables no ordenó (no hubo clic en flecha), usar el dropdown
        if not order_field and custom_ordering:
            ordering_map = {
                'titulo_asc': 'titulo',
                'titulo_desc': '-titulo',
                'vencimiento_asc': 'vencimiento',
                'vencimiento_desc': '-vencimiento',
                'duracion_asc': 'duracion',
                'duracion_desc': '-duracion',
            }
            order_field = ordering_map.get(custom_ordering)

        # 4. Aplicar el ordenamiento
        if order_field:
            queryset = queryset.order_by(order_field)
        else:
            # Orden por defecto si no se especifica (más nuevos primero)
            queryset = queryset.order_by('-id')
        # --- FIN DE SECCIÓN CORREGIDA ---

        # Total de registros DESPUÉS de aplicar los filtros
        records_filtered = queryset.count()

        # --- PAGINACIÓN ---
        # Paginación sobre el queryset ya filtrado y ordenado
        paginated_queryset = queryset[start: start + length]

        serializer = self.get_serializer(paginated_queryset, many=True)

        return Response({
            "draw": draw,
            "recordsTotal": records_total,
            "recordsFiltered": records_filtered,  # Corregido
            "data": serializer.data,
        })

    @action(detail=True, methods=['post'], url_path='iniciar')
    def iniciar(self, request, pk=None):
        """Inicia una actividad basada en esta Tarea."""
        try:
            tarea = self.get_object()
            user = request.user

            # 1. Detener cualquier actividad actual del usuario
            actividad_actual = Actividades.objects.filter(
                user=user, fin=None).first()
            if actividad_actual:
                actividad_actual.fin = timezone.now()
                actividad_actual.save()

            # 2. Preparar comentario inicial
            # Tu index.html requiere >= 25 caracteres para poder DETENER la tarea.
            comentario_inicial = tarea.titulo
            if tarea.descripcion:
                # Usamos descripción si hay
                comentario_inicial = f"{tarea.descripcion}"

            if len(comentario_inicial) < 25:
                # Rellenamos con puntos si es muy corto
                comentario_inicial = comentario_inicial.ljust(25, '.')

            # Truncamos si es demasiado largo (límite de 500)
            comentario_inicial = comentario_inicial[:500]

            # 3. Crear la nueva actividad
            nueva_actividad = Actividades.objects.create(
                user=user,
                ot=tarea.ot,
                tarea=tarea,
                inicio=timezone.now(),
                fin=None,
                comentario=comentario_inicial
            )

            # 4. Actualizar el estado de la Tarea a "en progreso"
            tarea.estado = 'in_progress'
            tarea.save()

            # Serializamos y devolvemos la nueva actividad creada
            serializer = ActividadesSerializer(nueva_actividad)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class KanbanViewSet(viewsets.ReadOnlyModelViewSet):
    """API Tarea"""
    queryset = Tarea.objects.all().order_by('prioridad', 'vencimiento')
    serializer_class = TareaSerializer
    # Asegura que solo usuarios autenticados accedan
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = TareaFilter
    filterset_fields = ['ot', 'user']
    ordering_fields = ['titulo']

    @action(detail=False, methods=['get'], url_path='mi-kanban')
    def mi_kanban(self, request):
        """Devuelve las tareas del usuario autenticado en formato Kanban."""
        hoy = date.today()
        queryset = self.get_queryset().filter(user=request.user)

        tareas = []
        for tarea in queryset:
            if tarea.estado == 'done':
                if tarea.editado.date() == hoy:
                    tareas.append(tarea)
            else:
                tareas.append(tarea)

        serializer = self.get_serializer(tareas, many=True)
        return Response(serializer.data)


@login_required
def add_tarea(request):
    """Vista para agregar una nueva tarea"""
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        ot_id = request.POST.get('ot')  # Puede estar vacío
        prioridad = request.POST.get('prioridad')
        fecha_vencimiento = request.POST.get('vencimiento')  # YYYY-MM-DD
        user_id = request.POST.get('user')
        duracion_str = request.POST.get('duracion')  # Nombre corregido

        ot_instance = None
        user_instance = None
        duracion = None  # Inicializar duracion

        if ot_id:
            ot_instance = Ot.objects.filter(id_ot=ot_id).first()

        if user_id:
            user_instance = User.objects.filter(id=user_id).first()

        if duracion_str:  # Comprobar si la cadena no está vacía
            try:
                horas, minutos = map(int, duracion_str.strip().split(":"))
                duracion = timedelta(hours=horas, minutes=minutos)
            except (ValueError, TypeError):
                duracion = None  # Asignar None si el formato es incorrecto

        vencimiento = None
        if fecha_vencimiento:
            try:
                vencimiento = datetime.strptime(
                    fecha_vencimiento, "%Y-%m-%d")
            except ValueError:
                vencimiento = None  # Asignar None si el formato es incorrecto

        Tarea.objects.create(
            titulo=titulo,
            descripcion=descripcion,
            ot=ot_instance,
            vencimiento=vencimiento,
            prioridad=prioridad,
            user=user_instance,
            duracion=duracion
        )
        return redirect('tarea_lista')

    return JsonResponse({'error': 'Método no permitido'}, status=405)


class ActividadesViewSet(viewsets.ModelViewSet):
    """ViewSet para las actividades"""
    queryset = Actividades.objects.all().order_by('-id')
    permission_classes = [IsAuthenticated]
    serializer_class = ActividadesSerializer  # Serializer por defecto para CRUD

    def get_serializer_class(self):
        """
        Usa un serializer diferente para el dashboard
        """
        if self.action == 'dashboard_actividad':
            return ActividadesDashboardSerializer
        return ActividadesSerializer

    @action(detail=False, methods=['get'])
    def usuarios_sin_actividad(self, request):
        """Usuarios sin actividad, luego cambiar por una consulta de dashboard"""
        usuarios_con_actividad = Actividades.objects.filter(
            fin__isnull=True
        ).values_list('user_id', flat=True).distinct()

        usuarios_sin_actividad = User.objects.filter(
            is_active=True
        ).exclude(
            id__in=usuarios_con_actividad
        ).exclude(id=2)

        nombres = list(usuarios_sin_actividad.values_list(
            'username', flat=True))

        if settings.DEBUG:
            mensaje = ""
        else:
            if nombres:
                mensaje = (
                    "Los siguientes usuarios no han registrado actividad: " +
                    ", ".join(nombres)
                )
            else:
                mensaje = ""

        return Response({
            "mensaje": mensaje,
            "usuarios": nombres
        })

    @action(detail=True, methods=['post'])
    def reanudar(self, request, pk=None):
        """Reanuda una actividad"""
        original = self.get_object()
        user = request.user
        actividad = Actividades.objects.filter(
            user=user, fin=None).first()
        if actividad:
            actividad.fin = timezone.now()
            actividad.save()
        nueva_actividad = Actividades.objects.create(
            user=user,
            ot=original.ot,
            tarea=original.tarea,
            inicio=now(),
            fin=None,
            comentario=original.comentario
        )

        serializer = self.get_serializer(nueva_actividad)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def dashboard_actividad(self, request):
        """Vista para el dashboard de actividades actuales"""
        activos = User.objects.filter(is_active=True)
        # Subconsulta para obtener el id de la última actividad por usuario
        ultimas_actividades_ids = Actividades.objects.filter(
            user=OuterRef('pk')
        ).order_by('-id').values('id')[:1]
        # Obtener las actividades usando los ids obtenidos
        actividades = Actividades.objects.filter(
            id__in=Subquery(
                activos.annotate(
                    last_act_id=Subquery(ultimas_actividades_ids)
                ).values('last_act_id')
            )
        )
        # Usa ActividadesDashboardSerializer aquí automáticamente
        serializer = self.get_serializer(actividades, many=True)
        return Response(serializer.data)


class InformesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para informes"""
    queryset = Actividades.objects.all().order_by('-id')
    permission_classes = [IsAuthenticated]
    serializer_class = InformesSerializer

    @action(detail=False, methods=['get'])
    def detallado(self, request):
        """DataTables"""

        draw = int(request.GET.get("draw", 1))
        start = int(request.GET.get("start", 0))  # Caracter 'A' eliminado
        length = int(request.GET.get("length", 10))
        search_value = request.GET.get("search[value]", "").strip()
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        # Filtrar si hay un término de búsqueda
        queryset = self.get_queryset().filter(fin__isnull=False)
        if search_value:
            queryset = queryset.filter(
                Q(descripcion__icontains=search_value) |
                Q(ot__id_ot__icontains=search_value) |
                Q(ot__nombre__icontains=search_value) |
                Q(tarea__titulo__icontains=search_value) |
                Q(user__username__icontains=search_value))
        if start_date and end_date:
            queryset = queryset.filter(
                inicio__date__range=[start_date, end_date]
            )
        total_count = queryset.count()

        # Paginación manual con Django Paginator
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

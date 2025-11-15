# pylint: disable=no-member
"""Muchas Vistas"""
import json
import os
from datetime import datetime, date, timedelta
from collections import defaultdict
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from django.utils.timezone import now
from django.db.models import Q, Sum
from django.contrib.auth.models import User
from auth.models import Colaborador
from intranet.forms import EventosForm, ExpedientesForm
from intranet.models import Expedientes, Ot, TipOt, Eventos
from kanban.models import Actividades
from kanban.forms import ActividadesForm, TareaForm


@ensure_csrf_cookie
def csrf_token_view(request):
    return JsonResponse({'message': 'CSRF cookie set'})


@login_required
def list_actividades_index(request):
    """Endpoint para cargar actividades en index.html con DataTables."""

    # 1. Parámetros de DataTables
    draw = int(request.GET.get("draw", 1))
    start = int(request.GET.get("start", 0))
    # Longitud de página, 50 por defecto en tu JS
    length = int(request.GET.get("length", 10))
    search_value = request.GET.get("search[value]", "").strip()

    # 2. Queryset Base: Actividades del usuario actual y finalizadas
    # Modificamos la lógica que era muy lenta en 'index'
    queryset = Actividades.objects.filter(
        user=request.user.id,
        fin__isnull=False
    ).order_by('-id')

    # 3. Aplicar Filtro de Búsqueda
    if search_value:
        queryset = queryset.filter(
            Q(comentario__icontains=search_value) |
            Q(ot__id__icontains=search_value) |
            Q(tarea__titulo__icontains=search_value)
        )

    records_filtered = queryset.count()
    records_total = records_filtered
    queryset = queryset[start:start + length]
    data = []
    for actividad in queryset:
        expediente = Expedientes.objects.filter(
            ot=actividad.ot).order_by('-id').first()
        data.append({
            'id': actividad.id,
            'actividad_desc': actividad.tarea.titulo if actividad.tarea else actividad.descripcion,
            'comentario': actividad.comentario,
            'expediente_estado': expediente.estado if expediente else None,
            'expediente_numero': expediente.numero if expediente else None,
            'expediente_reingreso': expediente.reingreso.strftime('%Y-%m-%d') if expediente and expediente.reingreso else None,
            'expediente_vencimiento': expediente.vencimiento.strftime('%Y-%m-%d') if expediente and expediente.vencimiento else None,
            'ot': f"{actividad.ot.id} - {actividad.ot.nombre}" if actividad.ot else None,
            'inicio': actividad.inicio.strftime('%H:%M') if actividad.inicio else None,
            'fin': actividad.fin.strftime('%H:%M') if actividad.fin else None,
            'fecha': actividad.inicio.strftime('%Y-%m-%d') if actividad.inicio else None,
            'total': actividad.total(),
        })
    return JsonResponse({
        "draw": draw,
        "recordsTotal": records_total,
        "recordsFiltered": records_filtered,
        "data": data,
    })


@login_required
def index(request):
    """ Index """
    form = ActividadesForm(user=request.user)
    id = request.user.id

    tracker = Actividades.objects.filter(user=id, fin=None).first()
    if tracker:
        ribbon = Expedientes.objects.filter(
            ot=tracker.ot).order_by('-id').first()
    else:
        ribbon = None
    context = {
        'title': 'Ingresar Actividades',
        'tracker': tracker,
        'ribbon': ribbon,
        'form': form
    }
    return render(request, 'index.html', context)


def end_actividad(request):
    """Finalizar Actividad"""
    if request.method == 'POST':
        id = request.POST.get('id')
        com_act = request.POST.get('comentario')
        try:
            actividades = Actividades.objects.get(id=id)
            actividades.comentario = com_act
            actividades.fin = timezone.now()
            actividades.save()
            messages.success(request, "Actividad finalizada con exito")
        except Exception:
            messages.error(request, "Error")
        return redirect('index')


def calendario(request):
    """Calendario"""
    form = EventosForm()
    context = {
        'title': 'Calendario',
        'form': form,
    }
    return render(request, 'calendario.html', context)


def dashboard(request):
    """Template Dashboard"""
    ots_today = Actividades.objects.filter(
        inicio__date=date.today()
    )
    total_tasks = ots_today.values('ot').distinct().count()
    total_seconds = 0
    total_horas_diarias = defaultdict(float)
    for actividad in ots_today:
        if actividad.inicio:
            if actividad.fin:
                diferencia_horas = actividad.fin - actividad.inicio
            else:
                diferencia_horas = timezone.now() - actividad.inicio

            # Calcular la diferencia en segundos
            segundos_totales = diferencia_horas.total_seconds()
            total_seconds += segundos_totales
            total_horas_diarias[actividad.inicio.date(
            )] += segundos_totales / 3600  # Convertir a horas

    total_hours = total_seconds // 3600
    total_minutes = (total_seconds % 3600) // 60
    total_productivity_hours = f"{int(total_hours)}:{int(total_minutes)}"
    total_projects = Ot.objects.filter(estado="activo").count()
    total_members = User.objects.filter(is_active=True).count()
    labels = list(total_horas_diarias.keys())  # Fechas
    chart = list(total_horas_diarias.values())  # Horas trabajadas por día
    context = {
        'total_projects': total_projects,
        'total_tasks': total_tasks,
        'total_members': total_members,
        'total_productivity': total_productivity_hours,
        'total_horas_diarias': total_horas_diarias,
        'labels': labels,
        'chart': chart
    }
    return render(request, 'dashboard.html', context)


@login_required
def proyectos(request):
    """ Proyectos """
    if request.method == 'POST':
        tipo_proyecto_id = request.POST.get('txtTipoProyecto', None)
        tipo_proyecto = TipOt.objects.get(
            id=tipo_proyecto_id) if tipo_proyecto_id else None
        try:
            nac_ot_str = request.POST.get('txtFecha', None)

            ot = Ot(
                id=request.POST.get('txtOT', None),
                nombre=request.POST.get('txtProyecto', None),
                color=request.POST.get('txtColor', None),
                inicio=nac_ot_str,
                id_tipot=tipo_proyecto
            )
            ot.save()

            messages.success(request, "OT y sus ingresos creados con éxito.")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
        return redirect('proyecto_detalle', id=ot.id)

    tipos_proyecto = TipOt.objects.all().order_by('nom_tipo')
    ots_list = Ot.objects.all().order_by('-id')
    ots = []

    for ot in ots_list:
        expediente = Expedientes.objects.filter(
            ot=ot.id).order_by('-id').first()
        ot.expediente = expediente
        ots.append(ot)

    context = {
        'title': 'Proyectos',
        'ots': ots,
        'tipos_proyecto': tipos_proyecto,
        'today': date.today(),  # esto pasa la fecha de hoy al template
    }
    return render(request, 'proyectos.html', context)


def edit_proyecto(request, id_ot):
    """ Editar Proyecto """
    ot = get_object_or_404(Ot, id=id_ot)
    if request.method == 'POST':
        nombre = request.POST.get('txtNombre')
        estado = request.POST.get('sltEstado')
        color = request.POST.get('color')
        descripcion = request.POST.get('txtDescripcion', '')
        privado = int(request.POST.get('chkPrivado', 0))
        try:
            ot.nombre = nombre
            ot.estado = estado
            ot.color = color
            ot.descripcion = descripcion
            ot.privado = privado
            ot.save()
            messages.success(request, "OT editado con éxito")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
        return redirect('proyecto_detalle', id_ot=id_ot)


def delete_proyecto(request):
    """Eliminar Proyecto"""
    if request.method == 'POST':
        id = request.POST.get('id', None)
        try:
            ot = Ot.objects.get(id=id)
            ot.delete()
            messages.success(request, "OT eliminado con éxito")
        except Ot.DoesNotExist:
            messages.error(request, "OT no encontrado")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
        return redirect('proyectos')


@login_required
def proyecto_detalle(request, id_ot):
    """ Proyectos Detalle """
    ot = Ot.objects.get(pk=id_ot)
    form = TareaForm()
    actividades = Actividades.objects.filter(ot_id=id_ot)
    total_timedelta = timedelta()
    for act in actividades:
        if act.inicio and act.fin:
            hora_limite = act.inicio.replace(
                hour=8, minute=0, second=0, microsecond=0)
            inicio = act.inicio if act.inicio >= hora_limite else hora_limite
            diferencia = act.fin - inicio
            total_timedelta += diferencia
    total_horas = int(total_timedelta.total_seconds() // 3600)
    total_minutos = int((total_timedelta.total_seconds() % 3600) // 60)
    total_horas_registradas = f"{total_horas:02}:{total_minutos:02}"

    context = {
        'form': form,
        'ot': ot,
        'total_horas_registradas': total_horas_registradas,
    }
    return render(request, 'proyecto_detallado.html', context)


def obtener_notificaciones(request):
    today = now().date()
    seven_days_later = today + timedelta(days=7)

    # Obtener vencimientos y reingresos desde Expedientes
    vencimientos = list(Expedientes.objects.filter(
        ~Q(estado__in=["Inscrito", "Tachado"]),
        Q(vencimiento__range=[today, seven_days_later]) |
        Q(reingreso__range=[today, seven_days_later])
    ).select_related('ot')
        .values('ot__id', 'vencimiento', 'reingreso', 'entidad', 'ot__nombre', 'estado')
        .order_by('vencimiento'))
    activos = User.objects.filter(is_active=True).values_list('id', flat=True)
    # Obtener cumpleaños de colaboradores
    cumple = list(Colaborador.objects.filter(
        Q(nacimiento__month=today.month, nacimiento__day__gte=today.day) |
        Q(nacimiento__month=seven_days_later.month,
          nacimiento__day__lte=seven_days_later.day),
        user__in=activos
    ).select_related('user')
        .values('user__first_name', 'user__last_name', 'nacimiento'))

    # Leer los feriados desde un archivo JSON
    json_path = os.path.join(os.path.dirname(
        __file__), "../../static/docs/feriados.json")

    try:
        with open(json_path, "r", encoding="utf-8") as file:
            feriados = json.load(file)
    except FileNotFoundError:
        feriados = []

    # Filtrar feriados dentro de los próximos 7 días
    feriados_proximos = [
        f for f in feriados if today <= datetime.strptime(f["date"], "%Y-%m-%d").date() <= seven_days_later
    ]
    eventos = list(Eventos.objects.filter(
        inicio__date__range=[today, seven_days_later]
    ).select_related('usuario')
     .values('titulo', 'inicio', 'usuario__first_name', 'usuario__last_name'))
    return JsonResponse({
        "vencimientos": vencimientos,
        "cumple": cumple,
        "feriados": feriados_proximos,
        "eventos": eventos
    })


@login_required
def expedientes(request):
    """ Expedientes """
    estados = Expedientes.ESTADOS
    form = ExpedientesForm()
    context = {
        'estados': estados,
        'form': form,
    }
    return render(request, 'expedientes.html', context)

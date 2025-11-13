"""Vista del equipo, area, login y logout"""
import json
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import AreaSerializer, UserSerializer, ColaboradorSerializer, Select2Serializer
from .models import Colaborador, Area
from .forms import AddUserForm, EditUserForm, CustomPasswordChangeForm, AddAreaForm, EditAreaForm, CustomSetPasswordForm


@login_required
def equipo_admin_view(request):
    """ Lista de colaboradores y áreas """
    add_form = AddUserForm()
    edit_form = EditUserForm()
    add_area_form = AddAreaForm()
    edit_area_form = EditAreaForm()
    # Obtiene solo los colaboradores, no todos los usuarios
    colaboradores = Colaborador.objects.select_related(
        'user', 'area').order_by('-user__is_active')
    areas = Area.objects.all()  # 🔹 Obtenemos todas las áreas

    context = {
        'add_form': add_form,
        'edit_form': edit_form,
        'add_area_form': add_area_form,
        'edit_area_form': edit_area_form,
        'colaboradores': colaboradores,  # Ahora con área incluida
        'areas': areas
    }
    return render(request, 'admin/equipo.html', context)


@login_required
def equipo_user_view(request):
    """ Lista de colaboradores """
    colaboradores = User.objects.filter(is_active=True).order_by('-is_active')
    areas = Area.objects.all()  # Obtener todas las áreas
    context = {
        'title': 'Equipo',
        'colaboradores': colaboradores,
        'areas': areas  # Pasar las áreas al template
    }
    return render(request, 'user/equipo.html', context)


def add_equipo(request):
    """Añadir nuevo trabajador"""
    if request.method == 'POST':
        form = AddUserForm(request.POST)
        if form.is_valid():
            User.objects.create_user(
                first_name=form.cleaned_data['first_name'],
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
            )
    return redirect('equipo')


@login_required
def edit_equipo(request):
    """Editar trabajador"""
    if request.method == 'POST':
        print(request.POST)
        # Obtener el username del formulario
        user_id = request.POST.get('id')
        if not user_id:
            messages.error(request, "Error: No se recibió el ID del usuario.")
            return redirect('equipo')
        user = get_object_or_404(User, id=user_id)

        try:
            # Buscar al usuario por su username
            user = get_object_or_404(User, id=user_id)
            # Obtener otros datos del formulario
            first_name = request.POST.get('first_name')
            username = request.POST.get('username')
            last_name = request.POST.get('last_name')
            nac_col = request.POST.get('drpFc')  # Fecha de nacimiento
            id_area = request.POST.get('id_are')  # Área seleccionada
            # Verificar si la casilla de superusuario está marcada
            is_superuser = 'is_superuser' in request.POST

            # Convertir la fecha de nacimiento a formato datetime
            if nac_col:
                nac_col = datetime.strptime(nac_col, '%d/%m/%Y').date()
            else:
                nac_col = None

            # Actualizar los datos del usuario
            user.first_name = first_name
            user.username = username
            user.last_name = last_name
            user.is_superuser = is_superuser  # Cambiar el estado de superusuario
            user.save()  # Guardar los cambios del usuario

            # Actualizar los datos del colaborador
            colaborador = get_object_or_404(Colaborador, user=user)
            colaborador.nac_col = nac_col
            colaborador.id_are = Area.objects.get(
                id_are=id_area)  # Actualizar el área seleccionada
            colaborador.save()  # Guardar los cambios del colaborador

            messages.success(request, "Usuario editado con éxito")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

        return redirect('equipo')  # Redirigir a la página de equipo

    return render(request, 'equipo.html', {
        'areas': Area.objects.all(),  # Pasar todas las áreas disponibles
    })


def add_area(request):
    """Añadir area"""
    if request.method == "POST":
        form = AddAreaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('equipo')
    return redirect('equipo')


def edit_area(request):
    """Editar area"""
    if request.method == "POST":
        try:
            area_id = request.POST.get("id_are")
            cod_are = request.POST.get("cod_are")
            nom_are = request.POST.get("nom_are")

            if not area_id or not cod_are or not nom_are:
                return HttpResponse("Datos incompletos", status=400)

            area = get_object_or_404(Area, id=area_id)
            area.codigo = cod_are
            area.nombre = nom_are
            area.save()

            # 🚀 Redirigir a la misma página después de editar
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

        except Exception as e:
            return HttpResponse(f"Error: {str(e)}", status=500)

    # Si la petición no es POST, redirigir o mostrar un error
    return HttpResponse("Método no permitido", status=405)


def delete_area(request, id):
    area = get_object_or_404(Area, id_are=id)
    area.delete()
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


def perfil(request, id):
    # Buscar el usuario por ID o mostrar 404
    usuario = get_object_or_404(User, id=id)
    context = {
        'usuario': usuario,
        'title': 'Perfil'}
    return render(request, 'perfil.html', context)


def perfil_detalle(request, id_user):
    """Perfil Detallado"""
    perfil = User.objects.get(id=id_user)

    colaborador = Colaborador.objects.get(id=id_user)
    area = colaborador.area
    context = {
        'perfil': perfil,
        'colaborador': colaborador,
        'area': area,
    }

    return render(request, 'admin/perfil_detallado.html', context)


def actualizar_foto_perfil(request, usuario_id):
    """Actualizar foto de Perfil"""
    colaborador = Colaborador.objects.get(user=usuario_id)

    if request.method == 'POST' and request.FILES.get('foto'):
        colaborador.foto = request.FILES['foto']
        colaborador.save()
        return redirect('perfil_detalle', id_user=usuario_id)

    return render(request, 'perfil.html', {'colaborador': colaborador})


@login_required
def cambiar_contrasena(request):
    if request.method == "POST":
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Evita que se cierre la sesión
            update_session_auth_hash(request, user)
            messages.success(
                request, "Tu contraseña ha sido cambiada con éxito.")
            # Cambia "perfil" por la URL a donde quieras redirigir
            return redirect("login")
        else:
            messages.error(
                request, "Hubo un error en el formulario. Inténtalo nuevamente.")
    else:
        form = CustomPasswordChangeForm(user=request.user)

    return render(request, "cambiar_contraseña.html", {"form": form})


def cambiar_contrasena_usuario(request, usuario_id):
    usuario = get_object_or_404(User, pk=usuario_id)
    if request.method == 'POST':
        form = CustomSetPasswordForm(user=usuario, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Contraseña cambiada correctamente.")

            # Redirigir al detalle del perfil del usuario
            # Redirige al perfil detallado
            return redirect('perfil_detalle', id_user=usuario.id)
    else:
        form = CustomSetPasswordForm(user=usuario)

    return render(request, 'admin/cambiar_contraseña_equipo.html', {'form': form, 'usuario': usuario})


def login_view(request):
    """ This is the login view, it will render the login.html template """
    if request.method == 'POST':
        user = authenticate(
            request, username=request.POST['username'], password=request.POST['password'])
        if user is not None:
            login(request, user)
            return redirect('index')
        return render(request, 'auth/login.html', {
            'error': 'Usuario o contraseña incorrectos'
        })
    return render(request, 'auth/login.html')


@login_required
def logout_view(request):
    """ This is the logout view """
    logout(request)
    return redirect('login')


@csrf_exempt
def cambiar_estado(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('user_id')

        try:
            user = User.objects.get(id=user_id)
            # Cambiar el estado de is_active
            user.is_active = not user.is_active
            user.save()
            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Usuario no encontrado'})
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
def actualizar_perfil(request, usuario_id):
    # Obtener al usuario seleccionado a partir del ID
    user = get_object_or_404(User, id=usuario_id)

    if request.method == 'POST':

        # Recoger los valores del formulario, si no están vacíos
        first_name = request.POST.get('firstname')
        last_name = request.POST.get('lastname')
        email = request.POST.get('useremail')

        dni = request.POST.get('dni')
        fec_nac = request.POST.get('fec_nac')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        tip_cuenta = request.POST.get('tip_cuenta')
        num_cuenta = request.POST.get('num_cuenta')
        is_superuser = 'is_superuser' in request.POST
        id_are = request.POST.get('id_are')
        biografia = request.POST.get('biografia')
        nom_emergencia = request.POST.get('nom_emergencia')
        telf_emergencia = request.POST.get('telf_emergencia')
        # Actualizar solo los campos que han sido modificados
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name

        if email:
            user.email = email
        user.is_superuser = is_superuser
        user.save()
        print("ID de Área recibido:", id_are)

        # Actualizar los datos del colaborador asociado con ese usuario, si se proporcionan
        colaborador = Colaborador.objects.get(user=user)

        # Verificar y actualizar los campos, si están vacíos, asignarles None
        colaborador.dni = dni if dni else None
        colaborador.nacimiento = fec_nac if fec_nac else None
        colaborador.telefono = telefono if telefono else None
        colaborador.direccion = direccion if direccion else None
        colaborador.tip_cuenta = tip_cuenta if tip_cuenta else None
        colaborador.num_cuenta = num_cuenta if num_cuenta else None
        colaborador.biografia = biografia if biografia else None
        colaborador.nom_emergencia = nom_emergencia if nom_emergencia else None
        colaborador.telf_emergencia = telf_emergencia if telf_emergencia else None

        # Aquí obtenemos la instancia del Area usando el ID recibido del formulario
        if id_are:
            try:
                # Buscar la instancia de Area correspondiente al id_are
                area = Area.objects.get(id=id_are)
                colaborador.area = area  # Asignamos la instancia de Area
            except Area.DoesNotExist:
                # Dejarlo vacío si no se encuentra el área
                colaborador.area = None
        else:
            # Si no se envió un id_are, asignamos None para eliminar el valor
            colaborador.area = None
        print("ID de Área recibido:", id_are)
        colaborador.save()

        # Redirigir a una página de confirmación o éxito
        return redirect('perfil_detalle', id_user=usuario_id)

    # Si es GET, mostrar el formulario con los datos del usuario seleccionado
    return render(request, 'admin/perfil_detallado.html', {'perfil': user, 'colaborador': user.colaborador})


def guardar_calificacion(request):
    if request.method == 'POST':  # Verifica que el método sea POST
        colaborador_id = request.POST.get('colaborador_id')
        rating = request.POST.get('rating')

        # Verifica si colaborador_id y rating son válidos
        if colaborador_id and rating is not None:
            try:
                rating = float(rating)  # Convertir el rating a flotante
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Calificación no válida'}, status=400)

            # Obtén el colaborador utilizando el ID
            colaborador = get_object_or_404(
                Colaborador, user=colaborador_id)

            # Actualiza la calificación en el modelo Colaborador
            colaborador.calificacion = rating
            colaborador.save()

            # Si todo sale bien, retorna una respuesta exitosa
            return JsonResponse({'success': True, 'message': 'Calificación guardada correctamente'})

        return JsonResponse({'success': False, 'message': 'Datos no válidos'}, status=400)

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)


def check_username(request):
    username = request.GET.get('username', '')
    user_exists = User.objects.filter(username=username).exists()
    return JsonResponse({'exists': user_exists})


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Esta cosa la utiliza cotizaciones"""
    queryset = User.objects.filter(is_active=True).order_by('username')
    serializer_class = UserSerializer


class UsersSelectViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para los usuarios en el select2"""
    serializer_class = Select2Serializer

    def get_queryset(self):
        qs = User.objects.filter(is_active=True).order_by('username')
        search = self.request.query_params.get('q', None)
        if search:
            qs = qs.filter(username__icontains=search)
        return qs


class ColaboradorViewSet(viewsets.ModelViewSet):
    """Colaborador"""
    queryset = Colaborador.objects.all()
    serializer_class = ColaboradorSerializer
    permission_classes = [IsAuthenticated]


class AreaViewSet(viewsets.ModelViewSet):
    """Area"""
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [IsAuthenticated]

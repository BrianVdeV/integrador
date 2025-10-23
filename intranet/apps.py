import threading
import time
from django.apps import AppConfig
from django.utils import timezone


def cerrar_actividades_automaticamente():
    from kanban.models import Actividades  # IMPORTA AQUÍ DENTRO
    from django.utils.timezone import is_aware, make_naive
    while True:
        ahora = timezone.localtime(timezone.make_aware(timezone.now()))

        if ahora.hour == 18 and ahora.minute >= 35:
            actividades_en_curso = Actividades.objects.filter(
                fin__isnull=True)
            if actividades_en_curso.exists():
                for actividad in actividades_en_curso:
                    if is_aware(ahora):
                        ahora = make_naive(ahora)

                    actividad.fin = ahora
                    actividad.save()
                    print(
                        f"Actividad {actividad.id} cerrada a las {actividad.fin}")
        time.sleep(60)  # Espera 60 segundos antes de verificar nuevamente


class IntranetConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'intranet'

    def ready(self):
        hilo = threading.Thread(
            target=cerrar_actividades_automaticamente, daemon=True)
        hilo.start()

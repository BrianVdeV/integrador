import threading
import time
from django.apps import AppConfig
from django.utils import timezone


class IntranetConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'intranet'

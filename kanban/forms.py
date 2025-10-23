"""Formularios Kanban"""
from datetime import date
from django import forms
from intranet.models import User, Ot
from .models import Tarea


class TareaForm(forms.Form):
    """Formulario para crear eventos"""
    titulo = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "id": "titulo"}
        )
    )
    prioridad = forms.ChoiceField(
        choices=Tarea.PRIORITY_CHOICES, initial='low',
        widget=forms.Select(
            attrs={"class": "form-select", "id": "sltPrioridad"})
    )
    ot = forms.ModelChoiceField(
        queryset=Ot.objects.filter(estado='Activo').order_by('-id_ot'),
        widget=forms.Select(
            attrs={"class": "form-select", "id": "sltOt"}),
        required=False,
    )
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('username'),
        widget=forms.Select(
            attrs={"class": "form-select", "id": "sltUsuario"}),
        required=False,
    )
    descripcion = forms.CharField(widget=forms.Textarea(
        attrs={"class": "form-control", "id": "txtDescripcion", "rows": "3"}), required=False)
    vencimiento = forms.DateField(
        widget=forms.DateInput(
            attrs={"class": "form-control", "id": "txtVencimiento", "type": "date"}),
    )
    hora = forms.TimeField(
        widget=forms.TimeInput(
            attrs={"class": "form-control", "id": "txtHora", "type": "time"}),
        required=False
    )
    duracion = forms.DurationField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "id": "duracion", "placeholder": "hh:mm",
                   "data-toggle": "input-mask", "data-mask-format": "00:00"}
        )
    )


class ActividadesForm(forms.Form):
    """Formulario Actividades"""
    ot = forms.ModelChoiceField(
        queryset=Ot.objects.none(),
        widget=forms.Select(
            attrs={"class": "form-select", "id": "sltOT"}),
        empty_label=None,
        required=True
    )
    tarea = forms.ModelChoiceField(
        queryset=Tarea.objects.none(),
        widget=forms.Select(
            attrs={"class": "form-select", "id": "sltTarea"}),
        required=False,
    )
    descripcion = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "id": "descripcion"}
        )
    )
    comentario = forms.CharField(
        widget=forms.Textarea(
            attrs={"class": "form-control", "id": "comentario", "rows": "3"}
        )
    )
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('username'),
        widget=forms.Select(
            attrs={"class": "form-select", "id": "sltUsuario"}),
        required=False,
    )
    inicio = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"class": "form-control",
                   "id": "inicio", "type": "datetime-local"}
        )
    )
    fin = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"class": "form-control",
                   "id": "fin",  "type": "datetime-local"}
        )
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user and user.is_superuser:
            qs = Ot.objects.filter(estado="Activo").order_by("-id_ot")
        else:
            qs = Ot.objects.filter(
                estado="Activo", privado=0).order_by("-id_ot")

        self.fields["ot"].queryset = qs

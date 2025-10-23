"""Formularios"""
from django import forms
from django.contrib.auth.models import User
from .models import Ot,Expedientes


class EventosForm(forms.Form):
    """Formulario para crear eventos"""
    titulo = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"class": "form-control", "id": "txtEvento"}))
    inicio = forms.DateField(
        widget=forms.DateInput(
            attrs={"class": "form-control", "id": "txtInicio", "type": "date"}),
        required=False
    )
    hora = forms.TimeField(
        widget=forms.TimeInput(
            attrs={"class": "form-control", "id": "txtHora", "type": "time"}),
        required=False
    )
    fin = forms.DateField(
        widget=forms.DateInput(
            attrs={"class": "form-control", "id": "txtFin", "type": "date"}),
        required=False
    )
    horaFin = forms.TimeField(
        widget=forms.TimeInput(
            attrs={"class": "form-control", "id": "txtHoraFin", "type": "time"}),
        required=False
    )
    ot = forms.ModelChoiceField(
        queryset=Ot.objects.filter(estado='Activo').order_by('-id_ot'),
        widget=forms.Select(
            attrs={"class": "form-select", "id": "sltOt"}),
        required=False,
    )
    usuario = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('username'),
        widget=forms.Select(
            attrs={"class": "form-select", "id": "sltUsuario"}),
        required=False,
    )
    descripcion = forms.CharField(widget=forms.Textarea(
        attrs={"class": "form-control", "id": "txtDescripcion", "rows": "2"}), required=False)



class ExpedientesForm(forms.Form):
    """Expedientes"""
    ot = forms.ModelChoiceField(
        queryset=Ot.objects.filter(estado='Activo').order_by('-id_ot'),
        widget=forms.Select(
            attrs={"class": "form-select", "id": "ot"}),
        empty_label=None,
    )
    numero = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "id": "numero"}
        )
    )
    estado = forms.ChoiceField(
        choices=Expedientes.ESTADOS,
        widget=forms.Select(
            attrs={"class": "form-select", "id": "estado"})
    )
    entidad = forms.ChoiceField(
        choices=Expedientes.ENTIDAD,
        widget=forms.Select(
            attrs={"class": "form-select", "id": "entidad"})
    )
    presentacion = forms.DateField(
        widget=forms.DateInput(
            attrs={"class": "form-control", "id": "presentacion", "type": "date"}),
        required=False
    )
    reingreso = forms.DateField(
        widget=forms.DateInput(
            attrs={"class": "form-control", "id": "reingreso", "type": "date"}),
        required=False
    )
    vencimiento = forms.DateField(
        widget=forms.DateInput(
            attrs={"class": "form-control", "id": "vencimiento", "type": "date"}),
        required=False
    )

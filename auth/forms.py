from django import forms
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from .models import Area


class AddAreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ["codigo", "nombre"]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
        }


class EditAreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ["id", "codigo", "nombre"]


class AddUserForm(forms.Form):
    """Formulario en Equipo"""
    first_name = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))
    username = forms.CharField(
        max_length=50, widget=forms.TextInput(attrs={"class": "form-control"}))
    password1 = forms.CharField(
        max_length=50, widget=forms.PasswordInput(attrs={"class": "form-control"}))


class EditUserForm(forms.Form):
    """Formulario en Equipo"""
    id = forms.IntegerField(widget=forms.HiddenInput())

    first_name = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"class": "form-control", "id": "txtNombres"}))

    last_name = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"class": "form-control", "id": "txtApellidos"}))

    username = forms.CharField(
        max_length=50, widget=forms.TextInput(attrs={"class": "form-control", "id": "txtUsuario"}))

    # Campo Fecha de Nacimiento
    nac_col = forms.DateField(
        widget=forms.DateInput(
            attrs={"class": "form-control", "id": "drpFc", "type": "date"}),
        required=False
    )


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Contraseña actual",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Ingresa tu contraseña actual"}),
    )
    new_password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Ingresa tu nueva contraseña"}),
    )
    new_password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirma tu nueva contraseña"}),
    )


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Ingresa la nueva contraseña"}),
    )
    new_password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirma la nueva contraseña"}),
    )

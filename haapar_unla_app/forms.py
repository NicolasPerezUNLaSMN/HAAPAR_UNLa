from django import forms
from .models import Task
from django.utils.translation import gettext_lazy as _
from django.core.validators import validate_email
from haapar_unla_app.aplicaciones.casos_uso.registrar_usuario import RegistrarUsuario
from haapar_unla_app.infraestructura.persistencia.usuario_repositorio_db import UsuarioRepositorioDB
from django.contrib.auth import get_user_model


User = get_user_model()
    
# Para personalizar el formulario del registro de usuarios
class SignUpForm(forms.Form):
    username = forms.CharField(
        label=_("Nombre Completo"),
        max_length=255,
        widget=forms.TextInput(attrs={
            'placeholder': 'Nombre Completo',
            'class': 'form-control'
        }),
        required=True
    )

    first_name = forms.CharField(
        label=_("Nombre"),
        max_length=255,
        widget=forms.TextInput(attrs={
            'placeholder': 'Nombre',
            'class': 'form-control'
        }),
        required=True
    )

    last_name = forms.CharField(
        label=_("Apellido"),
        max_length=255,
        widget=forms.TextInput(attrs={
            'placeholder': 'Apellido',
            'class': 'form-control'
        }),
        required=True
    )

    email = forms.EmailField(
        label=_("Email"),
        max_length=100,
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'ejemplo@email.com', 
            'class': 'form-control'
        }),
        validators=[validate_email]
    )

    password = forms.CharField(
        label=_("Contraseña"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=12,
        required=True
    )

    password2 = forms.CharField(
        label=_("Confirmar contraseña"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )


    def clean_username(self):
        username = self.cleaned_data['username']
        repositorio = UsuarioRepositorioDB()
        if repositorio.existe_username(username):
            raise forms.ValidationError("Este usuario ya está registrado")
        return username


    def clean_email(self):
        email = self.cleaned_data['email']
        validate_email(email)
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está registrado.")
        return email

    def save(self):
        repo = UsuarioRepositorioDB()
        caso_uso = RegistrarUsuario(repo)
        return caso_uso.ejecutar(
            nombre=self.cleaned_data['first_name'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password']
        )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')

        if password and password2 and password != password2:
            raise forms.ValidationError(_("Las contraseñas no coinciden"))
        return cleaned_data

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 12:
            raise forms.ValidationError(_("La contraseña debe tener al menos 12 caracteres"))
        return password
    
    
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title','description','important']
        widgets = {
            'title': forms.TextInput(attrs={'class' : 'form-control', 'placeholder':'Escribe un titulo'}),
            'description': forms.Textarea(attrs={'class' : 'form-control', 'placeholder':'Escribe una descripcion'}),
            'important': forms.CheckboxInput(attrs={'class' : 'form-check-input'}),
        }


class TemaForm(forms.Form):
    nombre = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    descripcion = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=True
    )
    horizonte = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    territorio = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()
    
# Para personalizar el formulario del registro de usuarios
class SignUpForm(UserCreationForm):
    """
    Formulario de registro extendido basado en UserCreationForm de Django.
    Añade un campo de email y validaciones personalizadas.
    """
    email = forms.EmailField(
        label="Email",
        max_length=250,
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email', 'class': 'form-control'})
    )

    username = forms.CharField(
        label="Usuario",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Usuario', 'class': 'form-control'})
    )

    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'placeholder': 'Contraseña', 'class': 'form-control'}),
        required=True
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirmar contraseña', 'class': 'form-control'}),
        required=True
    )

    class Meta(UserCreationForm.Meta):
        """
        Clase Meta para configurar el formulario.
        """
        model = User
        # Incluye todos los campos de UserCreationForm y añade 'email'
        fields = ('username', 'email', 'password1', 'password2',)

    def clean_email(self):
        """
        Valida que el email no esté ya registrado por otro usuario.
        """
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está registrado.")
        return email

    def save(self, commit=True):
        """
        Guarda el usuario con el email proporcionado.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

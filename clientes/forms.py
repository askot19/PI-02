from django import forms
from django.contrib.auth.models import User

from .models import Cliente, PerfilUsuario


class CadastroForm(forms.Form):
    """Equivalente ao formulário de cadastro.php (cria um usuário do sistema)."""

    cpf = forms.CharField(label='CPF', max_length=14)
    nome = forms.CharField(label='Nome completo', max_length=100)
    email = forms.EmailField(label='Email')
    senha = forms.CharField(label='Senha', widget=forms.PasswordInput, min_length=6)

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Já existe um usuário cadastrado com este email.')
        return email

    def clean_cpf(self):
        cpf = self.cleaned_data['cpf']
        if PerfilUsuario.objects.filter(cpf=cpf).exists():
            raise forms.ValidationError('Já existe um usuário cadastrado com este CPF.')
        return cpf


class LoginForm(forms.Form):
    """Equivalente ao formulário de login.php."""

    email = forms.EmailField(label='Email')
    senha = forms.CharField(label='Senha', widget=forms.PasswordInput)


class ClienteForm(forms.ModelForm):
    """Equivalente ao formulário de formulario.php (cadastro de clientes)."""

    class Meta:
        model = Cliente
        fields = ['cpf', 'nome', 'email', 'telefone', 'sexo', 'data_nasc', 'cep', 'cidade', 'estado', 'endereco']
        widgets = {
            'sexo': forms.RadioSelect,
            'data_nasc': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_cpf(self):
        cpf = self.cleaned_data['cpf']
        if Cliente.objects.filter(cpf=cpf).exists():
            raise forms.ValidationError('Já existe um cliente cadastrado com este CPF.')
        return cpf


class ClienteEditForm(forms.ModelForm):
    """
    Equivalente ao formulário de edit.php / saveEdit.php.

    O CPF não é editável aqui porque é a chave primária do registro —
    diferente do PHP original, que permitia alterá-lo (o que na prática
    causava um `UPDATE ... WHERE cpf=<cpf antigo>` inconsistente).
    """

    class Meta:
        model = Cliente
        fields = ['nome', 'email', 'telefone', 'sexo', 'data_nasc', 'cep', 'cidade', 'estado', 'endereco']
        widgets = {
            'sexo': forms.RadioSelect,
            'data_nasc': forms.DateInput(attrs={'type': 'date'}),
        }

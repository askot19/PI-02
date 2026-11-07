from django.contrib.auth.models import User
from django.db import models


class Cliente(models.Model):
    """
    Equivalente à tabela `clientes` do banco `formulario_viva_cafe`
    (vivadatabase.sql) do projeto original em PHP.
    """

    class Sexo(models.TextChoices):
        FEMININO = 'feminino', 'Feminino'
        MASCULINO = 'masculino', 'Masculino'
        OUTRO = 'outro', 'Outro'

    cpf = models.CharField('CPF', max_length=14, primary_key=True)
    nome = models.CharField('Nome completo', max_length=100)
    email = models.EmailField('Email', max_length=110)
    telefone = models.CharField('Telefone', max_length=15)
    sexo = models.CharField('Sexo', max_length=20, choices=Sexo.choices)
    data_nasc = models.DateField('Data de nascimento')
    cep = models.CharField('CEP', max_length=9)
    cidade = models.CharField('Cidade', max_length=45)
    estado = models.CharField('Estado', max_length=45)
    endereco = models.CharField('Endereço', max_length=100)
    latitude = models.FloatField('Latitude', null=True, blank=True)
    longitude = models.FloatField('Longitude', null=True, blank=True)

    class Meta:
        ordering = ['-cpf']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return f'{self.nome} ({self.cpf})'


class PerfilUsuario(models.Model):
    """
    Guarda o CPF do usuário do sistema — equivalente ao restante da tabela
    `usuarios` do projeto original.

    A autenticação (email + senha) passa a ser feita pelo sistema de
    autenticação nativo do Django (django.contrib.auth), que faz o
    hash da senha em vez de guardá-la em texto puro como no PHP original.
    O e-mail do usuário é usado como "username".
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    cpf = models.CharField('CPF', max_length=14, unique=True)

    class Meta:
        verbose_name = 'Perfil de usuário'
        verbose_name_plural = 'Perfis de usuário'

    def __str__(self):
        return f'{self.user.email} ({self.cpf})'

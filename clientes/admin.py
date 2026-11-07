from django.contrib import admin

from .models import Cliente, PerfilUsuario


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('cpf', 'nome', 'email', 'telefone', 'cidade', 'estado')
    search_fields = ('cpf', 'nome', 'email')
    list_filter = ('estado', 'sexo')


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('cpf', 'user')
    search_fields = ('cpf', 'user__email')

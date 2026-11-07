from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('sair/', views.sair, name='sair'),
    path('sistema/', views.sistema, name='sistema'),
    path('formulario/', views.formulario, name='formulario'),
    path('lista/', views.lista, name='lista'),
    path('editar/<str:cpf>/', views.editar, name='editar'),
    path('deletar/<str:cpf>/', views.deletar, name='deletar'),

    # Fluxo de "Esqueci minha senha" (views prontas do Django, com
    # templates e textos adaptados ao visual e ao idioma do projeto).
    path(
        'esqueci-senha/',
        auth_views.PasswordResetView.as_view(
            template_name='clientes/senha_esqueci.html',
            email_template_name='clientes/senha_email.txt',
            subject_template_name='clientes/senha_email_assunto.txt',
            success_url=reverse_lazy('senha_reset_enviado'),
        ),
        name='senha_esqueci',
    ),
    path(
        'esqueci-senha/enviado/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='clientes/senha_enviado.html',
        ),
        name='senha_reset_enviado',
    ),
    path(
        'redefinir-senha/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='clientes/senha_redefinir.html',
            success_url=reverse_lazy('senha_reset_completo'),
        ),
        name='senha_redefinir',
    ),
    path(
        'redefinir-senha/concluido/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='clientes/senha_completo.html',
        ),
        name='senha_reset_completo',
    ),
]

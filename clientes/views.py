from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CadastroForm, ClienteEditForm, ClienteForm, LoginForm
from .models import Cliente, PerfilUsuario


def home(request):
    """Equivalente a home.php."""
    return render(request, 'clientes/home.html')


def cadastro(request):
    """Equivalente a cadastro.php (cria um usuário do sistema, não um cliente)."""
    if request.method == 'POST':
        form = CadastroForm(request.POST)
        if form.is_valid():
            dados = form.cleaned_data
            user = User.objects.create_user(
                username=dados['email'],
                email=dados['email'],
                password=dados['senha'],
                first_name=dados['nome'],
            )
            PerfilUsuario.objects.create(user=user, cpf=dados['cpf'])
            messages.success(request, 'Cadastro realizado com sucesso! Faça login para continuar.')
            return redirect('login')
    else:
        form = CadastroForm()
    return render(request, 'clientes/cadastro.html', {'form': form})


def login_view(request):
    """Equivalente a login.php + testLogin.php."""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            senha = form.cleaned_data['senha']
            user = authenticate(request, username=email, password=senha)
            if user is not None:
                login(request, user)
                return redirect('sistema')
            messages.error(request, 'Email ou senha inválidos.')
    else:
        form = LoginForm()
    return render(request, 'clientes/login.html', {'form': form})


def sair(request):
    """Equivalente a sair.php."""
    logout(request)
    return redirect('login')


@login_required
def sistema(request):
    """Equivalente a sistema.php."""
    return render(request, 'clientes/sistema.html')


@login_required
def formulario(request):
    """Equivalente a formulario.php (cadastro de clientes)."""
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cadastro realizado com sucesso!')
            return redirect('formulario')
        messages.error(request, 'Erro ao cadastrar. Verifique os dados informados.')
    else:
        form = ClienteForm()
    return render(request, 'clientes/formulario.html', {'form': form})


@login_required
def lista(request):
    """Equivalente a lista.php (com busca por CPF, nome ou email)."""
    termo = request.GET.get('search', '').strip()
    clientes = Cliente.objects.all()
    if termo:
        clientes = clientes.filter(
            Q(cpf__icontains=termo) | Q(nome__icontains=termo) | Q(email__icontains=termo)
        )
    return render(request, 'clientes/lista.html', {'clientes': clientes, 'termo': termo})


@login_required
def editar(request, cpf):
    """Equivalente a edit.php + saveEdit.php."""
    cliente = get_object_or_404(Cliente, cpf=cpf)
    if request.method == 'POST':
        form = ClienteEditForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente atualizado com sucesso!')
            return redirect('lista')
    else:
        form = ClienteEditForm(instance=cliente)
    return render(request, 'clientes/editar.html', {'form': form, 'cliente': cliente})


@login_required
@require_POST
def deletar(request, cpf):
    """
    Equivalente a delete.php.

    Diferente do original (que excluía via link GET, vulnerável a CSRF),
    aqui a exclusão só acontece via POST + token CSRF do Django.
    """
    cliente = get_object_or_404(Cliente, cpf=cpf)
    cliente.delete()
    messages.success(request, 'Cliente excluído com sucesso!')
    return redirect('lista')

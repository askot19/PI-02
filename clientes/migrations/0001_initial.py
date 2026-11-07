from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Cliente',
            fields=[
                ('cpf', models.CharField(max_length=14, primary_key=True, serialize=False, verbose_name='CPF')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome completo')),
                ('email', models.EmailField(max_length=110, verbose_name='Email')),
                ('telefone', models.CharField(max_length=15, verbose_name='Telefone')),
                ('sexo', models.CharField(choices=[('feminino', 'Feminino'), ('masculino', 'Masculino'), ('outro', 'Outro')], max_length=20, verbose_name='Sexo')),
                ('data_nasc', models.DateField(verbose_name='Data de nascimento')),
                ('cidade', models.CharField(max_length=45, verbose_name='Cidade')),
                ('estado', models.CharField(max_length=45, verbose_name='Estado')),
                ('endereco', models.CharField(max_length=100, verbose_name='Endereço')),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
                'ordering': ['-cpf'],
            },
        ),
        migrations.CreateModel(
            name='PerfilUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cpf', models.CharField(max_length=14, unique=True, verbose_name='CPF')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Perfil de usuário',
                'verbose_name_plural': 'Perfis de usuário',
            },
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='cep',
            # Clientes já cadastrados recebem CEP em branco por padrão;
            # o campo passa a ser obrigatório para novos cadastros a partir
            # daqui (controlado pelo formulário, não pelo banco).
            field=models.CharField(default='', max_length=9, verbose_name='CEP'),
            preserve_default=False,
        ),
    ]

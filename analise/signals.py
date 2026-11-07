from django.db.models.signals import post_save
from django.dispatch import receiver

from clientes.models import Cliente


@receiver(post_save, sender=Cliente)
def geocodificar_cliente_automaticamente(sender, instance, **kwargs):
    """
    Sempre que um cliente é salvo sem latitude/longitude definidas, tenta
    geocodificar o endereço em segundo plano (best effort).

    Usa `.update()` (em vez de `instance.save()`) de propósito — isso evita
    disparar o próprio sinal de novo (loop infinito) e não gera uma segunda
    entrada no histórico do objeto.

    Se a API estiver fora do ar ou as dependências (requests) ainda não
    estiverem instaladas, o cadastro do cliente continua funcionando
    normalmente — só fica sem coordenadas por enquanto.
    """
    if instance.latitude is not None and instance.longitude is not None:
        return

    try:
        from .services import geocodificar_endereco
    except ImportError:
        return

    coordenadas = geocodificar_endereco(
        instance.endereco, instance.cidade, instance.estado, instance.cep
    )
    if coordenadas is None:
        return

    Cliente.objects.filter(pk=instance.pk).update(
        latitude=coordenadas[0], longitude=coordenadas[1]
    )

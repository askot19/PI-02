import time

from django.core.management.base import BaseCommand
from django.db.models import Q

from clientes.models import Cliente


class Command(BaseCommand):
    help = (
        'Geocodifica (obtém latitude/longitude) os clientes que ainda não '
        'têm coordenadas salvas, usando a API pública Nominatim. Respeita '
        'o limite de 1 requisição por segundo do serviço — para muitos '
        'clientes, pode demorar alguns minutos.'
    )

    def handle(self, *args, **options):
        try:
            from analise.services import geocodificar_endereco
        except ImportError:
            self.stderr.write(self.style.ERROR(
                "A biblioteca 'requests' não está instalada. Rode "
                "'pip install -r requirements.txt' dentro do seu ambiente "
                "virtual e tente de novo."
            ))
            return

        clientes = Cliente.objects.filter(
            Q(latitude__isnull=True) | Q(longitude__isnull=True)
        )
        total = clientes.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS(
                'Todos os clientes já têm coordenadas. Nada a fazer.'
            ))
            return

        self.stdout.write(f'Geocodificando {total} cliente(s)...')
        sucesso = 0

        for indice, cliente in enumerate(clientes, start=1):
            coordenadas = geocodificar_endereco(
                cliente.endereco, cliente.cidade, cliente.estado, cliente.cep
            )
            if coordenadas:
                cliente.latitude, cliente.longitude = coordenadas
                cliente.save(update_fields=['latitude', 'longitude'])
                sucesso += 1
                self.stdout.write(f'  [{indice}/{total}] {cliente.nome}: OK')
            else:
                self.stdout.write(self.style.WARNING(
                    f'  [{indice}/{total}] {cliente.nome}: endereço não encontrado'
                ))

            if indice < total:
                time.sleep(1)  # respeita o limite de uso do Nominatim

        self.stdout.write(self.style.SUCCESS(
            f'Concluído: {sucesso}/{total} clientes geocodificados com sucesso.'
        ))

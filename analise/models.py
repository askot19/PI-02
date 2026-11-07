from django.db import models  # noqa: F401

# Este app não define modelos próprios: ele lê e escreve latitude/longitude
# diretamente em clientes.models.Cliente e calcula tudo o mais em tempo real
# (com cache) em analise/services.py. Nenhuma tabela nova é necessária.

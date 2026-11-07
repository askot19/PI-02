from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import render

from .services import analisar_concentracao_sorocaba

CACHE_KEY = 'analise:resultado_sorocaba'
CACHE_TIMEOUT = 60 * 30  # 30 minutos


@login_required
def mapa_analise(request):
    """
    Exibe o mapa de análise de concentração de clientes em Sorocaba.

    O resultado fica em cache por 30 minutos (a análise reprocessa DBSCAN e
    faz chamadas externas de geocodificação reversa, então não vale a pena
    recalcular a cada acesso). Use ?atualizar=1 para forçar um recálculo.

    Só o resultado COMPLETO (dependências instaladas e clientes
    suficientes) é guardado em cache. Um resultado incompleto — faltando
    dependência ou sem clientes geocodificados ainda — nunca é cacheado,
    para não deixar o usuário preso numa tela de erro por 30 minutos depois
    de corrigir o problema (ex.: instalar uma biblioteca ou gerar clientes).
    """
    forcar_atualizacao = request.GET.get('atualizar') == '1'

    resultado = None if forcar_atualizacao else cache.get(CACHE_KEY)
    if resultado is None:
        resultado = analisar_concentracao_sorocaba()
        if resultado.get('dependencias_ok') and resultado.get('clientes_suficientes'):
            # Se algum nome de região falhou na consulta ao Nominatim, o
            # resultado vale por pouco tempo (2 min) para a próxima visita
            # tentar completar os nomes; caso contrário, 30 minutos.
            todos_nomeados = all(
                r.get('nome_regiao') != 'Região não identificada'
                for r in resultado.get('regioes_oportunidade', [])
            )
            cache.set(CACHE_KEY, resultado, CACHE_TIMEOUT if todos_nomeados else 120)

    return render(request, 'analise/mapa.html', {'resultado': resultado})

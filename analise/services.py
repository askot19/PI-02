"""
Módulo de análise geográfica de clientes.

Fluxo:
  1. Geocodificação: transforma o endereço de cada cliente em coordenadas
     (latitude/longitude), usando a API pública Nominatim (OpenStreetMap).
  2. Clustering (DBSCAN): identifica os "polos" onde já existe concentração
     de clientes — grupos de pontos próximos entre si.
  3. Grade de oportunidade: cobre a área da cidade com uma malha de células
     e conta quantos clientes caem em cada uma. As células com poucos
     clientes — mas ainda dentro da área de interesse — são sugeridas como
     alvo de campanhas de marketing.

Os imports de `requests`, `numpy` e `scikit-learn` são feitos dentro das
funções (e não no topo do arquivo) de propósito: assim, se essas
dependências ainda não tiverem sido instaladas (`pip install -r
requirements.txt`), o restante do site continua funcionando normalmente —
só esta análise fica indisponível, com uma mensagem clara para o usuário.
"""
import math
import time

from django.core.cache import cache

from clientes.models import Cliente

# Coordenadas aproximadas da área urbana de Sorocaba/SP. Usadas apenas como
# referência (não são obrigatórias): os limites reais da análise são
# calculados a partir dos próprios clientes já geocodificados.
SOROCABA_LAT = -23.5015
SOROCABA_LON = -47.4526

NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
NOMINATIM_REVERSE_URL = 'https://nominatim.openstreetmap.org/reverse'
# A política de uso do Nominatim exige um User-Agent identificável e no
# máximo 1 requisição por segundo — respeitamos os dois abaixo.
NOMINATIM_HEADERS = {
    'User-Agent': 'VivaCafeRestaurante-ProjetoUnivesp/1.0 (uso educacional)',
}

RAIO_TERRA_KM = 6371.0

# Controle de ritmo das chamadas ao Nominatim (máx. 1 requisição/segundo).
_INTERVALO_NOMINATIM_S = 1.1
_ultima_chamada_nominatim = 0.0


def geocodificar_endereco(endereco, cidade, estado, cep):
    """
    Consulta a API Nominatim e retorna (latitude, longitude) para o
    endereço informado, ou None se não encontrar ou se a API/dependência
    não estiver disponível. Nunca levanta exceção — é "best effort".
    """
    try:
        import requests
    except ImportError:
        return None

    consulta = f"{endereco}, {cidade}, {estado}, {cep}, Brasil"
    params = {'q': consulta, 'format': 'json', 'limit': 1, 'countrycodes': 'br'}

    try:
        resposta = requests.get(
            NOMINATIM_URL, params=params, headers=NOMINATIM_HEADERS, timeout=8
        )
        resposta.raise_for_status()
        dados = resposta.json()
    except Exception:
        return None

    if not dados:
        return None

    try:
        return float(dados[0]['lat']), float(dados[0]['lon'])
    except (KeyError, ValueError, TypeError, IndexError):
        return None


def _reverse_geocodificar(lat, lon):
    """
    Retorna um nome aproximado de bairro/região para uma coordenada.

    - Respeita o limite do Nominatim (1 requisição por segundo).
    - Guarda o nome em cache por 24h, mas SÓ quando a consulta deu certo:
      falhas (timeout, erro de rede, dependência ausente) não são
      cacheadas, para a próxima análise tentar de novo.
    """
    global _ultima_chamada_nominatim

    chave_cache = f'analise:reverse_geo:{lat:.4f}:{lon:.4f}'
    nome_em_cache = cache.get(chave_cache)
    if nome_em_cache is not None:
        return nome_em_cache

    nome_padrao = 'Região não identificada'

    try:
        import requests
    except ImportError:
        return nome_padrao

    espera = _INTERVALO_NOMINATIM_S - (time.monotonic() - _ultima_chamada_nominatim)
    if espera > 0:
        time.sleep(espera)

    params = {'lat': lat, 'lon': lon, 'format': 'json', 'zoom': 16}
    try:
        _ultima_chamada_nominatim = time.monotonic()
        resposta = requests.get(
            NOMINATIM_REVERSE_URL, params=params, headers=NOMINATIM_HEADERS, timeout=8
        )
        resposta.raise_for_status()
        endereco = resposta.json().get('address', {})
    except Exception:
        return nome_padrao  # falha: não vai para o cache

    nome = (
        endereco.get('suburb')
        or endereco.get('neighbourhood')
        or endereco.get('city_district')
        or endereco.get('road')
        or nome_padrao
    )
    cache.set(chave_cache, nome, 60 * 60 * 24)
    return nome


def _haversine_km(lat1, lon1, lat2, lon2):
    """Distância em km entre duas coordenadas (fórmula de haversine)."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * RAIO_TERRA_KM * math.asin(math.sqrt(a))


def analisar_concentracao_sorocaba(tamanho_celula_km=1.0, limite_regioes=10):
    """
    Executa a análise completa e retorna um dicionário pronto para o
    template (todos os valores já são tipos simples — float/int/str/list —
    para poder ser guardado em cache sem problema).
    """
    try:
        import numpy as np
    except ImportError:
        return {'dependencias_ok': False}

    clientes = list(
        Cliente.objects.filter(cidade__iexact='Sorocaba')
        .exclude(latitude__isnull=True)
        .exclude(longitude__isnull=True)
    )

    if len(clientes) < 5:
        return {
            'dependencias_ok': True,
            'clientes_suficientes': False,
            'total_geocodificado': len(clientes),
        }

    coordenadas = np.array([[c.latitude, c.longitude] for c in clientes])

    # ------------------------------------------------------------------
    # 1) DBSCAN — identifica os polos onde os clientes já se concentram.
    #    Usamos a métrica haversine (distância real sobre a esfera
    #    terrestre) em vez de distância euclidiana simples, porque
    #    latitude/longitude não formam um plano cartesiano.
    # ------------------------------------------------------------------
    try:
        from sklearn.cluster import DBSCAN
    except ImportError:
        return {'dependencias_ok': False}

    eps_km = 0.8  # clientes a até 800 m viram parte do mesmo polo
    eps_rad = eps_km / RAIO_TERRA_KM
    coordenadas_rad = np.radians(coordenadas)

    modelo = DBSCAN(eps=eps_rad, min_samples=3, metric='haversine')
    rotulos = modelo.fit_predict(coordenadas_rad)

    clusters = []
    for rotulo in sorted(set(rotulos)):
        if rotulo == -1:
            continue  # ruído: cliente isolado, não faz parte de um polo
        pontos = coordenadas[rotulos == rotulo]
        centro_lat, centro_lon = pontos.mean(axis=0)
        clusters.append({
            'centro_lat': float(centro_lat),
            'centro_lon': float(centro_lon),
            'quantidade_clientes': int(len(pontos)),
        })
    clusters.sort(key=lambda c: -c['quantidade_clientes'])

    # ------------------------------------------------------------------
    # 2) Grade sobre a área com clientes — conta quantos clientes caem
    #    em cada célula.
    # ------------------------------------------------------------------
    margem_km = 1.5
    lat_min, lon_min = coordenadas.min(axis=0)
    lat_max, lon_max = coordenadas.max(axis=0)
    lat_media = (lat_min + lat_max) / 2

    passo_lat = tamanho_celula_km / 111.0
    passo_lon = tamanho_celula_km / (111.0 * math.cos(math.radians(lat_media)))
    margem_lat = margem_km / 111.0
    margem_lon = margem_km / (111.0 * math.cos(math.radians(lat_media)))

    lat_min -= margem_lat
    lat_max += margem_lat
    lon_min -= margem_lon
    lon_max += margem_lon

    linhas_lat = np.arange(lat_min, lat_max, passo_lat)
    linhas_lon = np.arange(lon_min, lon_max, passo_lon)

    lats_clientes = coordenadas[:, 0]
    lons_clientes = coordenadas[:, 1]
    raio_relevancia_km = 3.0  # ignora células muito longe de qualquer cliente

    celulas = []
    for lat in linhas_lat:
        for lon in linhas_lon:
            centro_lat = float(lat + passo_lat / 2)
            centro_lon = float(lon + passo_lon / 2)

            lat1, lon1 = map(math.radians, [centro_lat, centro_lon])
            lat2 = np.radians(lats_clientes)
            lon2 = np.radians(lons_clientes)
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = (
                np.sin(dlat / 2) ** 2
                + math.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
            )
            distancias = 2 * RAIO_TERRA_KM * np.arcsin(np.sqrt(a))
            distancia_minima = float(distancias.min())

            if distancia_minima > raio_relevancia_km:
                continue  # fora da área de interesse (ex.: zona rural distante)

            quantidade = int(
                np.sum(
                    (coordenadas[:, 0] >= lat) & (coordenadas[:, 0] < lat + passo_lat)
                    & (coordenadas[:, 1] >= lon) & (coordenadas[:, 1] < lon + passo_lon)
                )
            )

            celulas.append({
                'lat': centro_lat,
                'lon': centro_lon,
                'quantidade_clientes': quantidade,
                'distancia_km': round(distancia_minima, 2),
            })

    # ------------------------------------------------------------------
    # 3) Seleciona as células com menor concentração como sugestões.
    # ------------------------------------------------------------------
    celulas.sort(key=lambda c: (c['quantidade_clientes'], c['distancia_km']))
    regioes_oportunidade = celulas[:limite_regioes]
    for regiao in regioes_oportunidade:
        regiao['nome_regiao'] = _reverse_geocodificar(regiao['lat'], regiao['lon'])

    return {
        'dependencias_ok': True,
        'clientes_suficientes': True,
        'total_geocodificado': len(clientes),
        'clientes': [
            {'lat': c.latitude, 'lon': c.longitude, 'nome': c.nome} for c in clientes
        ],
        'clusters': clusters,
        'regioes_oportunidade': regioes_oportunidade,
        'bbox': {
            'lat_min': float(lat_min),
            'lat_max': float(lat_max),
            'lon_min': float(lon_min),
            'lon_max': float(lon_max),
        },
    }

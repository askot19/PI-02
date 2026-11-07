"""
Gera clientes fictícios para testar o módulo de análise de mercado
(clustering / DBSCAN em analise/services.py).

Propositalmente DESBALANCEADO: a maior parte dos clientes é distribuída
entre bairros "normais" de Sorocaba, enquanto Jardim Santa Rosália e
Jardim do Éden recebem só um punhado de clientes — o suficiente para a
ferramenta de análise apontar essas duas regiões como oportunidade de
marketing.

As coordenadas de cada cliente são geradas diretamente (um ponto aleatório
próximo ao centro aproximado do bairro), SEM chamar a API de geocodificação
(Nominatim) — geocodificar 1000 endereços um por um, a 1 requisição por
segundo, levaria mais de 15 minutos e não seria um uso adequado de um
serviço público gratuito para dados que nem são reais. Os nomes, CPFs,
e-mails e telefones são inteiramente fictícios (os e-mails usam o domínio
"@teste.vivacafe.local", fácil de identificar e limpar depois com
--limpar).

As coordenadas dos bairros são aproximadas (para fins de teste, não para
uso oficial/cartográfico).
"""
import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from clientes.models import Cliente

# ---------------------------------------------------------------------------
# Bairros de Sorocaba: (nome, latitude_central, longitude_central, cep, peso)
# O "peso" define a proporção de clientes que cada bairro recebe entre si
# (não é população real — só um jeito de dar mais volume a alguns bairros
# maiores e variar a distribuição, para o mapa não ficar uniforme demais).
# ---------------------------------------------------------------------------
BAIRROS_SOROCABA = [
    ("Centro", -23.5017, -47.4581, "18010-000", 30),
    ("Vila Santana", -23.5000, -47.4650, "18035-000", 35),
    ("Vila Haro", -23.5050, -47.4550, "18040-000", 30),
    ("Vila Carol", -23.4650, -47.4600, "18075-000", 35),
    ("Jardim Vera Cruz", -23.4600, -47.4500, "18078-000", 30),
    ("Jardim São Paulo", -23.5150, -47.4600, "18045-000", 35),
    ("Parque Campolim", -23.5322, -47.4668, "18047-000", 45),
    ("Jardim América", -23.5450, -47.4600, "18055-000", 35),
    ("Jardim Emília", -23.5500, -47.4700, "18060-000", 30),
    ("Jardim Pagliato", -23.5400, -47.4800, "18065-000", 30),
    ("Vila Jardini", -23.5350, -47.4450, "18043-000", 25),
    ("Parque Esplanada", -23.5480, -47.4550, "18070-000", 30),
    ("Jardim Europa", -23.5420, -47.4450, "18048-000", 30),
    ("Jardim Astro", -23.4800, -47.4250, "18087-000", 30),
    ("Jardim Gonçalves", -23.4750, -47.4200, "18085-000", 30),
    ("Jardim Iguatemi", -23.4850, -47.4150, "18095-000", 35),
    ("Caguaçu", -23.4700, -47.4100, "18098-000", 25),
    ("Chácara Três Marias", -23.4900, -47.4180, "18090-000", 25),
    ("Jardim Guadalajara", -23.5050, -47.5000, "18110-000", 35),
    ("Wanel Ville", -23.5150, -47.5100, "18115-000", 30),
    ("Central Parque", -23.5000, -47.4950, "18108-000", 30),
    ("Jardim Simus", -23.5100, -47.5050, "18112-000", 25),
    ("Além Ponte", -23.4950, -47.4900, "18103-000", 30),
    ("Jardim Guarujá", -23.5000, -47.5050, "18120-000", 30),
    ("Jardim Paulistano", -23.4780, -47.4400, "18083-000", 25),
    ("Vila Helena", -23.4920, -47.4500, "18030-000", 30),
    ("Santa Cecília", -23.4980, -47.4700, "18052-000", 30),
    ("Residencial Aquarius", -23.5200, -47.4750, "18067-000", 25),
    ("Colina Verde", -23.5250, -47.4850, "18072-000", 20),
    ("Vila Xavier", -23.5100, -47.4400, "18041-000", 25),
]

# Bairros propositalmente com poucos clientes, para testar a ferramenta.
BAIRROS_BAIXA_CONCENTRACAO = [
    ("Jardim Santa Rosália", -23.4950, -47.4300, "18086-000", 4),
    ("Jardim do Éden", -23.5300, -47.4300, "18058-000", 3),
]

NOMES_MASCULINOS = [
    "João", "José", "Antônio", "Francisco", "Carlos", "Paulo", "Pedro",
    "Lucas", "Luiz", "Marcos", "Gabriel", "Rafael", "Daniel", "Marcelo",
    "Bruno", "Eduardo", "Felipe", "Rodrigo", "Gustavo", "Leonardo",
    "André", "Diego", "Thiago", "Fábio", "Renato", "Vinícius", "Matheus",
    "Caio", "Fernando", "Ricardo",
]

NOMES_FEMININOS = [
    "Maria", "Ana", "Francisca", "Antônia", "Adriana", "Juliana", "Márcia",
    "Fernanda", "Patrícia", "Aline", "Sandra", "Camila", "Amanda", "Bruna",
    "Jéssica", "Letícia", "Vanessa", "Mariana", "Gabriela", "Larissa",
    "Beatriz", "Carolina", "Renata", "Priscila", "Débora", "Cristina",
    "Simone", "Tatiane", "Rosana", "Elaine",
]

SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira",
    "Alves", "Pereira", "Lima", "Gomes", "Costa", "Ribeiro", "Martins",
    "Carvalho", "Almeida", "Lopes", "Soares", "Fernandes", "Vieira",
    "Barbosa", "Rocha", "Dias", "Nascimento", "Andrade", "Moreira",
    "Nunes", "Marques", "Machado", "Mendes", "Freitas", "Cardoso",
    "Ramos", "Gonçalves", "Santana", "Teixeira", "Correia", "Pinto",
    "Araújo", "Castro",
]

TIPOS_LOGRADOURO = ["Rua", "Avenida", "Alameda", "Travessa"]

NOMES_LOGRADOURO = [
    "das Flores", "São João", "Sete de Setembro", "Barão do Rio Branco",
    "Voluntários da Pátria", "José Ermínio de Moraes",
    "Doutor Miguel Petroni", "Padre Antônio Vieira", "dos Ipês",
    "Antônio Carlos Comitre", "Itavuvu", "General Osório",
    "Quinze de Novembro", "Duque de Caxias", "das Palmeiras",
    "dos Andradas", "Coronel Aureliano de Camargo", "das Acácias",
    "Monsenhor João Soares", "Doutor Campos Sales",
]

_MAPA_ACENTOS = str.maketrans(
    "áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ",
    "aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC",
)


def _remover_acentos(texto):
    return texto.translate(_MAPA_ACENTOS)


def _gerar_cpf_unico(cpfs_usados):
    """Gera um CPF com dígitos verificadores válidos (algoritmo público de
    checksum), mas inteiramente fictício — não corresponde a nenhuma
    pessoa real."""
    def digito_verificador(numeros):
        soma = sum(n * peso for n, peso in zip(numeros, range(len(numeros) + 1, 1, -1)))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    while True:
        numeros = [random.randint(0, 9) for _ in range(9)]
        d1 = digito_verificador(numeros)
        d2 = digito_verificador(numeros + [d1])
        todos = numeros + [d1, d2]
        cpf = "{}{}{}.{}{}{}.{}{}{}-{}{}".format(*todos)
        if cpf not in cpfs_usados:
            cpfs_usados.add(cpf)
            return cpf


def _gerar_email_unico(primeiro_nome, sobrenome, emails_usados):
    base = _remover_acentos(f"{primeiro_nome}.{sobrenome}").lower()
    tentativa = f"{base}@teste.vivacafe.local"
    contador = 1
    while tentativa in emails_usados:
        contador += 1
        tentativa = f"{base}{contador}@teste.vivacafe.local"
    emails_usados.add(tentativa)
    return tentativa


def _gerar_telefone():
    """Telefone de Sorocaba (DDD 15), alternando entre celular e fixo,
    já no mesmo formato que a máscara do site produz."""
    if random.random() < 0.7:  # celular é mais comum hoje em dia
        primeiro_grupo = "9" + "".join(str(random.randint(0, 9)) for _ in range(4))
    else:
        primeiro_grupo = str(random.randint(2, 5)) + "".join(str(random.randint(0, 9)) for _ in range(3))
    segundo_grupo = "".join(str(random.randint(0, 9)) for _ in range(4))
    return f"(15) {primeiro_grupo}-{segundo_grupo}"


def _gerar_data_nascimento():
    hoje = date.today()
    idade_em_dias = random.randint(18 * 365, 85 * 365)
    return hoje - timedelta(days=idade_em_dias)


def _gerar_cliente(nome_bairro, lat_centro, lon_centro, cep, cpfs_usados, emails_usados):
    sexo = random.choices(["feminino", "masculino", "outro"], weights=[47, 47, 6])[0]
    primeiro_nome = random.choice(NOMES_FEMININOS if sexo == "feminino" else NOMES_MASCULINOS)
    sobrenome1 = random.choice(SOBRENOMES)
    sobrenome2 = random.choice(SOBRENOMES)

    tipo_via = random.choice(TIPOS_LOGRADOURO)
    nome_via = random.choice(NOMES_LOGRADOURO)
    numero = random.randint(10, 2500)

    # Jitter de ~250m (desvio padrão) ao redor do centro do bairro, para os
    # clientes não ficarem todos empilhados exatamente no mesmo ponto.
    jitter_lat = random.gauss(0, 0.0025)
    jitter_lon = random.gauss(0, 0.0025)

    return Cliente(
        cpf=_gerar_cpf_unico(cpfs_usados),
        nome=f"{primeiro_nome} {sobrenome1} {sobrenome2}",
        email=_gerar_email_unico(primeiro_nome, sobrenome1, emails_usados),
        telefone=_gerar_telefone(),
        sexo=sexo,
        data_nasc=_gerar_data_nascimento(),
        cep=cep,
        cidade="Sorocaba",
        estado="SP",
        endereco=f"{tipo_via} {nome_via}, {numero} - {nome_bairro}",
        latitude=lat_centro + jitter_lat,
        longitude=lon_centro + jitter_lon,
    )


class Command(BaseCommand):
    help = (
        "Gera clientes fictícios distribuídos pelos bairros de Sorocaba, "
        "propositalmente desbalanceados (poucos clientes em Jardim Santa "
        "Rosália e Jardim do Éden), para testar o módulo de análise de "
        "mercado. As coordenadas são geradas diretamente, sem chamar a API "
        "de geocodificação — por isso a criação é rápida mesmo para 1000+ "
        "clientes. Todos os dados (nomes, CPFs, e-mails, telefones) são "
        "inteiramente fictícios."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--quantidade", type=int, default=1000,
            help="Quantos clientes gerar no total (padrão: 1000).",
        )
        parser.add_argument(
            "--limpar", action="store_true",
            help=(
                "Apaga os clientes de teste gerados anteriormente por este "
                "comando (identificados pelo e-mail terminado em "
                "@teste.vivacafe.local) antes de gerar os novos."
            ),
        )

    def handle(self, *args, **options):
        quantidade = options["quantidade"]

        if options["limpar"]:
            apagados, _ = Cliente.objects.filter(
                email__endswith="@teste.vivacafe.local"
            ).delete()
            self.stdout.write(self.style.WARNING(
                f"{apagados} cliente(s) de teste anterior(es) removido(s)."
            ))

        total_raros = sum(peso for *_resto, peso in BAIRROS_BAIXA_CONCENTRACAO)
        total_normais = quantidade - total_raros

        if total_normais < len(BAIRROS_SOROCABA):
            raise CommandError(
                f"--quantidade precisa ser pelo menos "
                f"{total_raros + len(BAIRROS_SOROCABA)} para cobrir todos "
                f"os bairros com pelo menos 1 cliente cada."
            )

        # Distribui total_normais proporcionalmente ao peso de cada bairro,
        # garantindo que a soma final seja EXATAMENTE total_normais (o
        # resto da divisão é distribuído entre os primeiros bairros).
        pesos = [peso for *_resto, peso in BAIRROS_SOROCABA]
        soma_pesos = sum(pesos)
        quantidades = [(total_normais * peso) // soma_pesos for peso in pesos]
        resto = total_normais - sum(quantidades)
        for i in range(resto):
            quantidades[i % len(quantidades)] += 1

        distribuicao = list(zip(BAIRROS_SOROCABA, quantidades))
        distribuicao += [(bairro, bairro[4]) for bairro in BAIRROS_BAIXA_CONCENTRACAO]

        cpfs_usados = set(Cliente.objects.values_list("cpf", flat=True))
        emails_usados = set(Cliente.objects.values_list("email", flat=True))

        self.stdout.write(f"Gerando {quantidade} cliente(s) fictício(s) em {len(distribuicao)} bairro(s)...")

        clientes_para_criar = []
        for (nome_bairro, lat_centro, lon_centro, cep, _peso), qtd in distribuicao:
            for _ in range(qtd):
                clientes_para_criar.append(
                    _gerar_cliente(nome_bairro, lat_centro, lon_centro, cep, cpfs_usados, emails_usados)
                )

        with transaction.atomic():
            Cliente.objects.bulk_create(clientes_para_criar, batch_size=200)

        self.stdout.write(self.style.SUCCESS(
            f"\n{len(clientes_para_criar)} cliente(s) fictício(s) criado(s) com sucesso.\n"
        ))
        self.stdout.write("Distribuição por bairro:")
        for (nome_bairro, *_resto), qtd in sorted(distribuicao, key=lambda item: -item[1]):
            marcador = " ⚠️  (baixa concentração, de propósito)" if qtd <= 5 else ""
            self.stdout.write(f"  {nome_bairro}: {qtd} cliente(s){marcador}")

        self.stdout.write(self.style.SUCCESS(
            "\nPronto! Acesse /analise/mapa/ no sistema para ver a análise "
            "com esses dados (não precisa rodar 'geocodificar_clientes' — "
            "as coordenadas já foram geradas direto)."
        ))

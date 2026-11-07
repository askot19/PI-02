# Viva Café & Restaurante — Backend em Django

Este projeto é a reescrita, em **Python + Django**, do backend que antes era
feito em **PHP puro + MySQLi**. Todas as telas e fluxos do sistema original
foram mantidos:

| Tela / fluxo               | Arquivo PHP original      | Equivalente em Django                          |
|-----------------------------|---------------------------|-------------------------------------------------|
| Página inicial               | `home.php`                | view `home` → `/`                               |
| Login                        | `login.php` + `testLogin.php` | view `login_view` → `/login/`               |
| Cadastro de usuário do sistema | `cadastro.php`          | view `cadastro` → `/cadastro/`                  |
| Logout                       | `sair.php`                 | view `sair` → `/sair/`                          |
| Painel logado                | `sistema.php`              | view `sistema` → `/sistema/`                    |
| Cadastro de cliente          | `formulario.php`           | view `formulario` → `/formulario/`              |
| Listagem/busca de clientes   | `lista.php`                | view `lista` → `/lista/`                        |
| Editar cliente               | `edit.php` + `saveEdit.php`| view `editar` → `/editar/<cpf>/`                |
| Excluir cliente              | `delete.php`               | view `deletar` → `/deletar/<cpf>/` (via POST)   |
| Esqueci minha senha          | *(não existia)*            | views prontas do Django → `/esqueci-senha/`     |
| Análise de mercado (clustering) | *(não existia)*          | app `analise` → `/analise/mapa/`                |
| Conexão com banco            | `config.php`               | `viva_cafe/settings.py` (`DATABASES`)           |
| Tabelas `clientes`/`usuarios`| `vivadatabase.sql`         | `clientes/models.py` (`Cliente`, `PerfilUsuario`) + migrations |

## Ambiente de desenvolvimento

Este projeto foi configurado para rodar da mesma forma que o Sistema de
Uniformes:

- **Versão do Django travada** (`Django==6.0.7` no `requirements.txt`, em vez
  de uma faixa de versões) — evita que uma atualização automática mude o
  comportamento do projeto sem você perceber.
- **`settings.py` simples**, no padrão de `django-admin startproject`: banco
  SQLite direto, sem variáveis de ambiente obrigatórias para rodar local
  (o suporte a PostgreSQL continua disponível, mas é opcional — veja a seção
  abaixo).
- **Scripts de setup** (`setup.sh` / `setup.bat`) que criam o `venv`,
  instalam as dependências e rodam as migrations em um único comando.
- **Pasta `.vscode/`** com `launch.json` (F5 já roda `manage.py runserver`
  com debug), `settings.json` e `extensions.json` recomendando a extensão
  Python — mesma experiência de abrir a pasta e apertar play.

## O que mudou (melhorias de segurança e boas práticas)

O código PHP original tinha vários problemas comuns em projetos didáticos,
que foram corrigidos na migração:

- **SQL Injection**: as queries eram montadas concatenando `$_GET`/`$_POST`
  diretamente na string SQL (`delete.php`, `edit.php`, `saveEdit.php`,
  `testLogin.php`, `formulario.php`). O Django ORM sempre usa consultas
  parametrizadas, então isso deixa de ser possível.
- **Senhas em texto puro**: a tabela `usuarios` guardava a senha sem hash.
  Agora a autenticação usa `django.contrib.auth`, que salva a senha com hash
  (PBKDF2) e nunca em texto puro.
- **Exclusão via link GET**: `delete.php` apagava um cliente ao simplesmente
  acessar uma URL (`<a href="delete.php?cpf=...">`), o que é vulnerável a
  CSRF. Agora a exclusão exige um `POST` autenticado com token CSRF.
- **Falta de proteção CSRF** em todos os formulários: todo formulário Django
  usa `{% csrf_token %}`.
- **CPF editável como chave primária** (`edit.php` permitia isso, e na
  prática o `UPDATE` do `saveEdit.php` ficava inconsistente). O formulário de
  edição agora trata o CPF como somente leitura.
- **Validação de dados**: agora feita com `forms.py` (Django Forms /
  ModelForms) no servidor, além dos atributos HTML `required`.

## Estrutura do projeto

```
viva_cafe_django/
├── manage.py
├── requirements.txt
├── viva_cafe/            # configurações do projeto (settings, urls, wsgi)
└── clientes/              # app com models, forms, views, urls, templates
    ├── models.py           # Cliente e PerfilUsuario
    ├── forms.py            # CadastroForm, LoginForm, ClienteForm, ClienteEditForm
    ├── views.py            # todas as views (equivalentes aos .php)
    ├── urls.py
    ├── admin.py
    ├── migrations/
    └── templates/clientes/ # home, login, cadastro, sistema, formulario, lista, editar
static/clientes/css/style.css   # CSS consolidado (mesmo visual do projeto original)
```

## Como rodar

### Caminho rápido (1 comando)

Na raiz do projeto:

- **macOS/Linux**: `bash setup.sh`
- **Windows**: `setup.bat` (dá duplo clique ou rode no terminal)

O script cria o `venv`, instala tudo do `requirements.txt` e roda as
migrations. No final, é só ativar o ambiente e subir o servidor:

```bash
# macOS/Linux
source venv/bin/activate
python manage.py runserver

# Windows
venv\Scripts\activate.bat
python manage.py runserver
```

### Passo a passo manual

1. Crie e ative um ambiente virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Rode as migrations (por padrão usa SQLite, sem precisar instalar nada):
   ```bash
   python manage.py migrate
   ```

4. (Opcional) Crie um superusuário para acessar `/admin/`:
   ```bash
   python manage.py createsuperuser
   ```

5. Suba o servidor de desenvolvimento:
   ```bash
   python manage.py runserver
   ```

6. Acesse `http://127.0.0.1:8000/` no navegador.

### Rodando no VSCode

O projeto já vem com uma pasta `.vscode/` configurada, no mesmo espírito do
Sistema de Uniformes:

- Abra a pasta `viva_cafe_django` no VSCode (`File > Open Folder`).
- Instale a extensão **Python** (a `.vscode/extensions.json` já sugere isso
  automaticamente).
- Depois de criar o `venv` (via `setup.sh`/`setup.bat` ou manualmente), abra
  a paleta de comandos (`Ctrl+Shift+P`) → **Python: Select Interpreter** →
  escolha o interpretador dentro de `./venv`.
- Pressione **F5** para rodar o servidor com debug (usa a configuração
  "Django: runserver" já pronta em `.vscode/launch.json`) — dá pra colocar
  breakpoints direto nas views.

### Usando PostgreSQL em vez de SQLite

O projeto já vem preparado para rodar com PostgreSQL, que é o banco
recomendado se você for além do ambiente local. Primeiro crie o banco:

```bash
createdb viva_cafe
# ou, dentro do psql:
# CREATE DATABASE viva_cafe;
```

Defina as variáveis de ambiente antes de rodar `migrate`/`runserver`:

```bash
export USE_POSTGRES=True
export DB_NAME=viva_cafe
export DB_USER=postgres
export DB_PASSWORD=sua_senha
export DB_HOST=localhost
export DB_PORT=5432
```

O driver (`psycopg`) já está no `requirements.txt`, então basta rodar:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

O Django cria as tabelas via `migrate` — não é preciso rodar
`vivadatabase.sql` manualmente; ele foi mantido no projeto (renomeado para
`vivadatabase_original.sql`) só como referência do schema original em MySQL.

## Identidade visual

O visual foi redesenhado com uma identidade própria do restaurante, em vez de
usar Bootstrap genérico:

- **Paleta**: café torrado (`#1c1108` → `#6f4e37`) como base escura, bordô
  (`#5c0f28` → `#9a1c3f`) como cor de ação/destaque, e dourado (`#c9a15a`)
  como acento de luxo. Cartões de formulário usam um creme quente
  (`#fbf4e9`) para contraste e legibilidade.
- **Tipografia**: `Fraunces` (serifada, itálica, expressiva) nos títulos —
  remete a um cardápio de restaurante fino — e `Work Sans` no corpo do
  texto, para leitura limpa em telas de sistema.
- **Assinatura**: os formulários (login, cadastro, cadastro de cliente,
  edição) são exibidos como uma "comanda" — um cartão com uma borda
  serrilhada no topo, como se fosse destacado de um bloco de pedidos — e a
  página inicial traz um selo sutil em forma de anel de café ao fundo.
- Bootstrap foi removido; todo o CSS agora é autoral e vive em
  `static/clientes/css/style.css`.

## Esqueci minha senha

O link **"Esqueci minha senha"** aparece na tela de login. O fluxo usa as
views prontas de `django.contrib.auth` (seguras e testadas, sem código
próprio para gerar tokens):

1. O usuário informa o e-mail em `/esqueci-senha/`.
2. Se o e-mail existir, o Django gera um link de redefinição válido por 24
   horas e o envia por e-mail.
3. **Em desenvolvimento**, esse e-mail não é enviado de verdade — ele é
   **impresso no terminal** onde o `python manage.py runserver` está
   rodando (procure por um bloco começando com `Content-Type: text/plain`
   logo após clicar em "Enviar link de redefinição"). Copie o link que
   aparece ali e cole no navegador.
4. O link leva para uma tela de nova senha; ao salvar, a senha antiga deixa
   de funcionar e o usuário já pode entrar com a nova.

### Configurando envio real de e-mail (produção)

Por padrão nenhum e-mail é enviado de verdade. Para usar um servidor SMTP
real (Gmail, SendGrid, um servidor da faculdade etc.), defina estas
variáveis de ambiente antes de rodar o servidor:

```bash
export EMAIL_HOST=smtp.seuservidor.com
export EMAIL_PORT=587
export EMAIL_HOST_USER=seu-usuario@dominio.com
export EMAIL_HOST_PASSWORD=sua-senha-ou-app-password
export EMAIL_USE_TLS=True
export DEFAULT_FROM_EMAIL="Viva Café & Restaurante <nao-responda@vivacafe.com>"
```

Assim que `EMAIL_HOST` estiver definido, o `settings.py` troca
automaticamente do modo "imprime no terminal" para o envio real via SMTP.

## Busca de endereço por CEP e máscaras de campo

O formulário de cadastro/edição de clientes agora tem um campo **CEP**. Ao
digitar os 8 números, o JavaScript busca o endereço automaticamente na API
pública [ViaCEP](https://viacep.com.br) e preenche **Endereço**, **Cidade**
e **Estado** — sem precisar de chave de API nem de configuração no backend
(a chamada acontece direto do navegador, com `fetch`). Se o CEP não for
encontrado, ou se a API estiver indisponível, uma mensagem avisa e os campos
continuam editáveis manualmente.

Além disso, os campos **CPF**, **CEP** e **Telefone** recebem máscara
automática enquanto o usuário digita (arquivo
`static/clientes/js/mascaras.js`, sem dependências externas):

| Campo     | Formato aplicado                                                   |
|-----------|----------------------------------------------------------------------|
| CPF       | `000.000.000-00`                                                      |
| CEP       | `00000-000`                                                            |
| Telefone  | `(00) 0000-0000` (residencial, 8 dígitos) ou `(00) 00000-0000` (celular, 9 dígitos) — o formato muda sozinho conforme a quantidade de números digitados |

Basta adicionar `data-mascara="cpf"`, `data-mascara="cep"` ou
`data-mascara="telefone"` a um `<input>` para ativar a máscara — o script já
é carregado em todas as páginas pelo `base.html`.

⚠️ Como o campo CEP foi adicionado depois da primeira versão do projeto, ele
veio como uma **migration nova** (`0002_cliente_cep`), não alterando a
`0001_initial`. Isso significa que rodar `python manage.py migrate` só
adiciona a coluna nova ao banco existente — nenhum cliente já cadastrado é
apagado. Clientes cadastrados antes dessa mudança ficam com CEP em branco
até que alguém edite o cadastro deles e preencha o campo.

## Análise de mercado (ciência de dados)

O app **`analise`** (`/analise/mapa/`, acessível pelo painel após o login)
identifica regiões de Sorocaba com baixa concentração de clientes,
para orientar campanhas de marketing. Funciona em três passos:

1. **Geocodificação** — o endereço de cada cliente (rua, cidade, estado,
   CEP) é convertido em coordenadas (latitude/longitude) usando a API
   pública [Nominatim / OpenStreetMap](https://nominatim.openstreetmap.org/),
   gratuita e sem necessidade de chave de API. Isso acontece automaticamente
   sempre que um cliente é cadastrado ou editado (via `post_save` signal em
   `analise/signals.py`) — se a API estiver fora do ar, o cadastro continua
   funcionando normalmente, só fica sem coordenadas por enquanto.
2. **Clustering com DBSCAN** — os clientes já geocodificados são agrupados
   com o algoritmo [DBSCAN](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html)
   (`scikit-learn`), usando distância geográfica real (métrica *haversine*)
   em vez de distância euclidiana simples. DBSCAN foi escolhido em vez de
   K-Means porque não é preciso decidir de antemão quantos grupos existem —
   ele descobre os "polos" onde já há concentração de clientes e marca
   pontos isolados como ruído.
3. **Grade de oportunidade** — a área coberta pelos clientes é dividida em
   uma grade de células de ~1km × 1km. Cada célula é contada quantos
   clientes tem dentro; as células com menos clientes — mas ainda dentro de
   até 3km de algum cliente existente, para não sugerir bairros fora da
   área de atuação — são listadas como sugestão de foco para marketing, com
   o nome aproximado da região (obtido por geocodificação reversa).

O resultado é mostrado num **mapa interativo** (biblioteca
[Leaflet](https://leafletjs.com/), também gratuita, carregada via CDN no
navegador) com os clientes, os polos identificados e as regiões sugeridas
em cores diferentes, seguido de uma tabela com o ranking de regiões.

### Preparando os dados existentes

Se você já tinha clientes cadastrados antes desta funcionalidade, rode uma
vez para localizá-los (respeita o limite de 1 requisição por segundo do
Nominatim, então pode demorar um pouco para muitos clientes):

```bash
python manage.py geocodificar_clientes
```

A análise em si só aparece completa a partir de 5 clientes de Sorocaba
geocodificados; com menos que isso, a tela mostra instruções em vez do mapa.

### Notas importantes

- A análise considera apenas clientes com o campo **Cidade** igual a
  "Sorocaba" (sem diferenciar maiúsculas/minúsculas).
- O resultado fica em cache por 30 minutos (a análise reprocessa o
  clustering e faz chamadas externas de geocodificação reversa a cada
  cálculo). Use o link "Atualizar análise agora" na tela para forçar um
  recálculo.
- As dependências novas (`requests`, `numpy`, `scikit-learn`) foram
  adicionadas ao `requirements.txt` — depois de atualizar o projeto, rode
  `pip install -r requirements.txt` de novo dentro do seu `venv`. Se
  esquecer, o resto do sistema continua funcionando normalmente; só a tela
  de análise mostra um aviso pedindo para instalar as dependências.
- Por ser um serviço público e gratuito, o Nominatim tem limites de uso
  (1 requisição/segundo) e a precisão do endereço encontrado depende de
  como o endereço foi digitado no cadastro. Para um uso em produção com
  volume alto de clientes, vale considerar um provedor de geocodificação
  pago (Google Maps, Mapbox etc.).

### Gerando clientes fictícios para testar a ferramenta

Para testar a análise sem precisar cadastrar clientes manualmente (ou
esperar a geocodificação de verdade), há um comando que gera clientes
fictícios distribuídos por ~30 bairros reais de Sorocaba, **propositalmente
desbalanceados**: a maioria dos bairros recebe uma quantidade generosa de
clientes, enquanto **Jardim Santa Rosália** e **Jardim do Éden** recebem só
3–4 cada — o suficiente para a análise apontar essas duas regiões como
oportunidade de marketing.

```bash
python manage.py gerar_clientes_teste
```

Por padrão gera 1000 clientes. Para outra quantidade, ou para limpar os
dados de teste gerados antes de criar novos:

```bash
python manage.py gerar_clientes_teste --quantidade 500
python manage.py gerar_clientes_teste --limpar   # apaga os de teste e gera de novo
```

Pontos importantes sobre esse comando:

- **Não chama a API do Nominatim** — as coordenadas de cada cliente são
  geradas diretamente (um ponto aleatório próximo ao centro aproximado do
  bairro), então roda em segundos mesmo para 1000+ clientes, sem precisar
  do `geocodificar_clientes` depois.
- Todos os dados são **inteiramente fictícios**: nomes, CPFs (com dígito
  verificador matematicamente válido, mas não correspondem a pessoas
  reais), e-mails e telefones são gerados aleatoriamente. Os e-mails usam
  o domínio `@teste.vivacafe.local`, fácil de identificar — é por esse
  domínio que o `--limpar` sabe quais clientes remover.
- As coordenadas de cada bairro são aproximadas, só para fins de teste da
  ferramenta — não use esses dados para nada além de testar a análise.
- Testado localmente com 1000 clientes: a ferramenta encontra os polos
  esperados via DBSCAN e, na lista padrão de 10 regiões sugeridas exibida
  na tela, aparece pelo menos uma região próxima a Jardim Santa Rosália e
  uma próxima a Jardim do Éden.

### Problemas conhecidos e como foram resolvidos

- **Tela de "Dependências pendentes" mesmo com tudo instalado**: o
  resultado da análise fica em cache por 30 minutos. Se a página foi
  aberta uma vez antes de terminar de instalar `numpy`/`scikit-learn`, o
  erro ficava "preso" em cache — mesmo depois de instalar tudo direito, a
  mesma tela de erro continuava aparecendo. Corrigido de duas formas: (1)
  a view só guarda em cache um resultado **completo** (nunca um erro ou
  estado incompleto), e (2) as telas de erro agora também têm um link para
  tentar de novo (`?atualizar=1`), então nunca mais fica sem saída.
- **Mapa com ladrilhos quebrados / "Access blocked"**: o servidor gratuito
  `tile.openstreetmap.org` tem uma política de uso rígida
  ([osm.wiki/Blocked](https://operations.osmfoundation.org/policies/tiles/))
  pensada para uso bem esporádico, e bloqueia IPs que acessam repetidamente
  durante desenvolvimento/testes — o que é exatamente o que acontece ao
  testar essa tela várias vezes. A primeira tentativa de correção trocou
  para os tiles da CARTO, mas pouco depois a CARTO também passou a exigir
  chave de API até no plano gratuito (mudança de política deles, não
  específica deste projeto — ver
  [github.com/piotrmilcarz/historymapcard/issues/23](https://github.com/piotrmilcarz/historymapcard/issues/23)
  para outros projetos afetados pela mesma mudança). A solução definitiva
  foi trocar para o [OpenFreeMap](https://openfreemap.org): tiles
  vetoriais renderizados via **MapLibre GL** (com a ponte oficial
  `@maplibre/maplibre-gl-leaflet` para funcionar dentro do Leaflet),
  gratuito, sem chave de API e **sem limite de requisições** — o serviço
  existe justamente para resolver esse tipo de problema, mantido por
  doações. Os dados do mapa continuam vindo do OpenStreetMap; só a forma
  de renderizar os tiles mudou. Isso adiciona duas bibliotecas carregadas
  via CDN (`maplibre-gl.js` e `leaflet-maplibre-gl.js`), só na tela de
  análise — o resto do site não é afetado.
- **Mapa aparece, mas os pontos de clientes/polos/oportunidade somem**: bug
  conhecido do `@maplibre/maplibre-gl-leaflet`
  ([issue #87](https://github.com/maplibre/maplibre-gl-leaflet/issues/87)) —
  a camada de mapa-base dele não respeita direito a ordem de empilhamento
  (z-index) das panes do Leaflet, e pode acabar cobrindo os marcadores.
  Corrigido em duas frentes: o mapa-base agora reaproveita a `tilePane`
  padrão do Leaflet (`pane: 'tilePane'` na criação do `L.maplibreGL`) e o
  CSS força `.leaflet-gl-layer { z-index: 200 !important; }` como reforço.
- **Tela "Dependências pendentes" mesmo com tudo certo**: se o servidor
  Django ficar rodando continuamente (sem reiniciar) desde antes de uma
  correção de código ou de uma instalação de biblioteca, o processo antigo
  continua em memória com o cache/estado anterior. Sempre que atualizar o
  projeto (baixar um zip novo, trocar `requirements.txt`), pare o servidor
  por completo (Ctrl+C) e rode `python manage.py runserver` de novo — o
  autoreload do Django nem sempre detecta mudanças em pastas sincronizadas
  por serviços como OneDrive, por causa de como esses serviços mexem na
  data de modificação dos arquivos.

## Observações

- O cadastro de **usuário do sistema** (login) agora usa o `User` nativo do
  Django (`django.contrib.auth.models.User`), com o e-mail como identificador
  de login e o CPF guardado em `PerfilUsuario`, ligado 1-para-1 ao usuário.
- Os arquivos originais (`vivadatabase.mwb`, `vivadatabase.sql`) foram
  mantidos apenas como referência do esquema original; o schema real agora é
  controlado pelas migrations do Django.

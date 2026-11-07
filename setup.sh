#!/usr/bin/env bash
# Cria o ambiente virtual, instala as dependências e prepara o banco.
# Uso: bash setup.sh
set -e

cd "$(dirname "$0")"

echo "==> Criando ambiente virtual (venv)..."
python3 -m venv venv

echo "==> Ativando ambiente virtual..."
source venv/bin/activate

echo "==> Instalando dependências (requirements.txt)..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Rodando migrations..."
python manage.py migrate

echo ""
echo "Tudo pronto! Para rodar o servidor:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"

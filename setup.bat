@echo off
REM Cria o ambiente virtual, instala as dependencias e prepara o banco.
REM Uso: setup.bat

cd /d "%~dp0"

echo ==^> Criando ambiente virtual (venv)...
python -m venv venv

echo ==^> Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo ==^> Instalando dependencias (requirements.txt)...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo ==^> Rodando migrations...
python manage.py migrate

echo.
echo Tudo pronto! Para rodar o servidor:
echo   venv\Scripts\activate.bat
echo   python manage.py runserver

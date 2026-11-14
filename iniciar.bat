@echo off
setlocal
set "RAIZ=%~dp0"
set "PY=%RAIZ%backend\.venv\Scripts\python.exe"

if not exist "%PY%" (
  echo Ambiente virtual nao encontrado em backend\.venv
  echo Faca a instalacao uma vez: cd backend, python -m venv .venv, depois pip install -r requirements.txt
  pause
  exit /b 1
)

if not exist "%RAIZ%backend\.env" copy "%RAIZ%backend\.env.example" "%RAIZ%backend\.env" >nul

if not exist "%RAIZ%backend\instance\sabor_clic.db" (
  echo Criando o banco de dados pela primeira vez...
  pushd "%RAIZ%backend"
  "%PY%" -m flask --app run init-db --sim
  popd
)

start "Sabor e Clic - API" /D "%RAIZ%backend" cmd /k ""%PY%" run.py"
start "Sabor e Clic - Front" /D "%RAIZ%frontend" cmd /k ""%PY%" -m http.server 5500 --bind 127.0.0.1"

timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:5500
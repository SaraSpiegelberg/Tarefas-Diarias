@echo off
rem ==================================================
rem  Gera o executavel do Tarefas Diarias (Windows)
rem  Resultado: dist\TarefasDiarias.exe
rem ==================================================
cd /d "%~dp0"

echo [1/2] Gerando icone...
python gen_icon.py

echo [2/2] Compilando com PyInstaller...
python -m PyInstaller --noconfirm --clean --onefile --windowed --icon "assets\app.ico" --name "TarefasDiarias" tarefas.py

rem Copia o icone junto (a janela usa assets\app.ico ao lado do .exe)
if not exist "dist\assets" mkdir "dist\assets"
copy /y "assets\app.ico" "dist\assets\app.ico" >nul

echo.
echo Pronto! O app esta em:  dist\TarefasDiarias.exe
pause
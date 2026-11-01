@echo off
python -m pip install --only-binary=:all: pygame-ce pyinstaller
pyinstaller --noconfirm --onefile --windowed --name DeadMansDraw --add-data "assets;assets" main.py
echo.
echo Pronto! O jogo esta em dist\DeadMansDraw.exe
pause

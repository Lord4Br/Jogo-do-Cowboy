@echo off
cd /d "%~dp0"
title Dead Man's Draw
python -c "import pygame" 2>nul || python -m pip install --only-binary=:all: pygame-ce
python main.py
if errorlevel 1 pause

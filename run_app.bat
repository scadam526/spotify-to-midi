@echo off
echo Starting Spotify Piano to MIDI Converter...
cd /d "%~dp0"
call venv311\Scripts\activate
python app.py
pause

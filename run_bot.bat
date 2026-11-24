@echo off
cd /d D:\Python\projects
"D:\Python\python.exe" bot.py >> "%~dp0bot_run.log" 2>&1
pause

@echo off
echo Starting Telegram Food Receipt Bot...
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo Error: Virtual environment not found!
    echo Please run: python -m venv .venv
    echo Then run: .venv\Scripts\pip.exe install -r requirements.txt
    pause
    exit /b 1
)

REM Check if config.py exists
if not exist "config.py" (
    echo Error: config.py not found!
    echo Please copy config_template.py to config.py and fill in your details.
    pause
    exit /b 1
)

REM Run the bot
echo Running the bot...
.venv\Scripts\python.exe main_simple.py

pause

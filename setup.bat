@echo off
echo ======================================
echo Telegram Food Receipt Bot Setup
echo ======================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)
echo [OK] Python is available

REM Check if Docker is available
docker --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Docker is not available - will use local Python setup
    set DOCKER_AVAILABLE=false
) else (
    echo [OK] Docker is available
    set DOCKER_AVAILABLE=true
)

echo.
echo Choose setup method:
echo 1. Docker (recommended for production)
echo 2. Local Python (for development)
echo 3. Auto-detect (Docker if available, otherwise local)
echo.
set /p CHOICE="Enter your choice (1-3): "

if "%CHOICE%"=="1" (
    if "%DOCKER_AVAILABLE%"=="false" (
        echo [ERROR] Docker is not available but was requested
        echo Please install Docker Desktop first
        pause
        exit /b 1
    )
    goto :docker_setup
)

if "%CHOICE%"=="2" (
    goto :local_setup
)

if "%CHOICE%"=="3" (
    if "%DOCKER_AVAILABLE%"=="true" (
        goto :docker_setup
    ) else (
        goto :local_setup
    )
)

echo [ERROR] Invalid choice
pause
exit /b 1

:docker_setup
echo.
echo ======================================
echo Docker Setup
echo ======================================

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not available
    echo Please install Docker Desktop which includes Docker Compose
    pause
    exit /b 1
)
echo [OK] Docker Compose is available

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo [INFO] Creating .env file from template...
    if exist ".env.template" (
        copy ".env.template" ".env" >nul
        echo [OK] Created .env file
    ) else (
        echo # Environment variables for Telegram Food Receipt Bot > .env
        echo BOT_TOKEN=YOUR_BOT_TOKEN_HERE >> .env
        echo ALLOWED_USER_ID=123456789 >> .env
        echo LOG_LEVEL=INFO >> .env
        echo [OK] Created basic .env file
    )
    echo.
    echo [IMPORTANT] Please edit .env file with your actual values:
    echo 1. BOT_TOKEN: Get from @BotFather on Telegram
    echo 2. ALLOWED_USER_ID: Get from @userinfobot on Telegram
    echo.
    pause
)

REM Test Docker build
echo [INFO] Testing Docker build...
docker build -t food-receipt-bot-test . >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker build failed
    echo Please check Docker is running and try again
    pause
    exit /b 1
)
echo [OK] Docker build successful

echo.
echo [SUCCESS] Docker setup complete!
echo.
echo Next steps:
echo 1. Edit .env file with your bot token and user ID
echo 2. Run: docker-compose up -d
echo 3. View logs: docker-compose logs -f telegram-bot
echo.
echo Or use the PowerShell script:
echo   .\docker.ps1 deploy
echo.
goto :end

:local_setup
echo.
echo ======================================
echo Local Python Setup
echo ======================================

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)

REM Install requirements
echo [INFO] Installing Python packages...
.venv\Scripts\pip.exe install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install requirements
    pause
    exit /b 1
)
echo [OK] Python packages installed

REM Create configuration files
if not exist "config.py" (
    if exist "config_template.py" (
        echo [INFO] Creating config.py from template...
        copy "config_template.py" "config.py" >nul
        echo [OK] Created config.py
    )
)

if not exist ".env" (
    echo [INFO] Creating .env file from template...
    if exist ".env.template" (
        copy ".env.template" ".env" >nul
        echo [OK] Created .env file
    )
)

REM Run test
echo [INFO] Running test...
.venv\Scripts\python.exe test_receipt.py >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Test failed - please check configuration
) else (
    echo [OK] Test passed
)

echo.
echo [SUCCESS] Local setup complete!
echo.
echo Next steps:
echo 1. Edit config.py or .env file with your bot token and user ID
echo 2. Run: python main_simple.py
echo 3. Or use: run_bot.bat
echo.

:end
if exist ".env" (
    echo Configuration files created:
    if exist "config.py" echo   - config.py
    if exist ".env" echo   - .env
    echo.
    echo [IMPORTANT] Fill in your actual values:
    echo - BOT_TOKEN: Get from @BotFather on Telegram
    echo - ALLOWED_USER_ID: Get from @userinfobot on Telegram
)
echo.
pause

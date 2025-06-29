# Telegram Food Receipt Bot

A Python Telegram bot that generates realistic food receipts for working days and sends them as PNG images.

## Features

- Responds only to a specific authorized user
- Generates receipts for the last N working days (Monday-Friday only)
- Each receipt has randomized items, prices, and transaction details
- Sends each receipt as a separate PNG image
- Realistic REWE-style receipt format
- **Docker support** for easy deployment
- **Environment variable configuration** (.env files)
- **Production-ready** with logging and health checks

## Quick Start

### Option 1: Docker (Recommended)

1. **Setup**:
   ```bash
   # Copy environment template
   cp .env.template .env
   
   # Edit .env with your bot token and user ID
   nano .env
   ```

2. **Run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

3. **View logs**:
   ```bash
   docker-compose logs -f telegram-bot
   ```

### Option 2: Local Python

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Test the generator**:
   ```bash
   python test_receipt.py
   ```

3. **Configure**:
   - Create `.env` file or copy `config_template.py` to `config.py`
   - Fill in your bot token and user ID

4. **Run**:
   ```bash
   python main_simple.py
   ```

## Configuration

### Environment Variables (Recommended)

Create a `.env` file:
```env
BOT_TOKEN=1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
ALLOWED_USER_ID=123456789
LOG_LEVEL=INFO
```

### Configuration Priority

1. **Environment variables** (highest priority)
2. **`.env` file**
3. **`config.py` file** (lowest priority)

## Prerequisites

1. **Create a Telegram Bot**:
   - Message @BotFather on Telegram
   - Send `/newbot` command
   - Follow the instructions to create your bot
   - Save the bot token you receive

2. **Get your Telegram User ID**:
   - Message @userinfobot on Telegram
   - It will reply with your user ID
   - Alternatively, message @RawDataBot and look for "from" -> "id"

## Files Overview

- **`main_simple.py`** - Main bot application (pure Python, Docker-ready)
- **`main.py`** - Alternative version using wkhtmltopdf
- **`Dockerfile`** - Docker image definition
- **`docker-compose.yml`** - Development Docker setup
- **`docker-compose.prod.yml`** - Production Docker setup
- **`.env.template`** - Environment variables template
- **`.env`** - Your actual environment variables (create this)
- **`config_template.py`** - Configuration template (legacy)
- **`test_receipt.py`** - Test script
- **`requirements.txt`** - Python dependencies
- **`DOCKER.md`** - Detailed Docker documentation

## Docker Commands

### Windows (PowerShell)
```powershell
# Setup and deploy
.\docker.ps1 setup
.\docker.ps1 deploy

# View logs
.\docker.ps1 logs

# Production deployment
.\docker.ps1 deploy -Env prod
```

### Linux/Mac (Make)
```bash
# Setup and deploy
make setup
make deploy

# View logs  
make logs

# Production deployment
make prod-deploy
```

### Direct Docker Compose
```bash
# Development
docker-compose up -d
docker-compose logs -f

# Production
docker-compose -f docker-compose.prod.yml up -d
```

## Setup Instructions

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure the bot**:
   - Copy `config_template.py` to `config.py`
   - Replace `YOUR_BOT_TOKEN_HERE` with your actual bot token
   - Replace `123456789` with your actual Telegram user ID

3. **Run the bot**:
   ```bash
   python main.py
   ```

## Usage

Once the bot is running:

1. Start a chat with your bot on Telegram
2. Send `/start` to begin
3. Send messages like:
   - `food 5` - Generate receipts for the last 5 working days
   - `Food 3` - Generate receipts for the last 3 working days
   - `FOOD 1` - Generate receipt for the last working day

The bot will:
- Calculate working days (Monday-Friday only)
- Generate realistic-looking REWE receipts for each day
- Convert each receipt to a PNG image
- Send each image separately to the chat

## Troubleshooting

- **wkhtmltopdf not found**: Make sure wkhtmltopdf is installed and in your PATH
- **Bot doesn't respond**: Check that your bot token is correct
- **"Not authorized" message**: Verify your user ID is correct
- **Images look weird**: The HTML-to-image conversion might need adjustment for your system

## Security Notes

- The bot only responds to one specific user ID for security
- Keep your bot token secret
- Don't share your config.py file

## Customization

You can modify the following in `main.py`:
- `possible_items`: Add/remove items that can appear on receipts
- `html_template`: Modify the receipt appearance
- `MIN_RECEIPT_TOTAL`: Change minimum receipt total
- Time ranges, store information, etc.

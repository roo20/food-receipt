# Docker Setup Guide

This guide explains how to run the Telegram Food Receipt Bot using Docker and Docker Compose.

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose (usually included with Docker Desktop)

## Quick Start with Docker Compose

1. **Clone/Download the project**
2. **Create your environment file**:
   ```bash
   cp .env.template .env
   ```
3. **Edit the `.env` file** with your actual values:
   ```env
   BOT_TOKEN=1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   ALLOWED_USER_ID=123456789
   ```
4. **Start the bot**:
   ```bash
   docker-compose up -d
   ```

## Configuration Options

### Environment Variables

You can configure the bot using these environment variables:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `BOT_TOKEN` | Yes | Telegram bot token from @BotFather | `1234567890:ABC-DEF...` |
| `ALLOWED_USER_ID` | Yes | Your Telegram user ID | `123456789` |
| `LOG_LEVEL` | No | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |

### Configuration Methods (in order of priority)

1. **Environment variables** (highest priority)
2. **`.env` file**
3. **`config.py` file** (lowest priority)

## Docker Commands

### Development

```bash
# Build and start the bot
docker-compose up --build

# Start in detached mode (background)
docker-compose up -d

# View logs
docker-compose logs -f telegram-bot

# Stop the bot
docker-compose down

# Restart the bot
docker-compose restart
```

### Production

```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up -d

# Update and restart
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Docker Commands

```bash
# Build the image
docker build -t food-receipt-bot .

# Run the container
docker run -d \
  --name food-receipt-bot \
  --env-file .env \
  --restart unless-stopped \
  food-receipt-bot

# View logs
docker logs -f food-receipt-bot

# Stop and remove
docker stop food-receipt-bot
docker rm food-receipt-bot
```

## File Structure for Docker

```
FoodRecipt/
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Development compose file
├── docker-compose.prod.yml # Production compose file
├── .dockerignore           # Files to exclude from Docker build
├── .env.template           # Environment variables template
├── .env                    # Your actual environment variables (create this)
├── main_simple.py          # Main application
├── requirements.txt        # Python dependencies
├── logs/                   # Log files (auto-created)
└── refrances/             # Reference files
```

## Production Deployment

### Using Docker Compose (Recommended)

1. **Copy files to server**:
   ```bash
   scp -r . user@server:/opt/food-receipt-bot/
   ```

2. **Create production environment file**:
   ```bash
   cd /opt/food-receipt-bot
   cp .env.template .env
   nano .env  # Edit with your values
   ```

3. **Deploy**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Monitor**:
   ```bash
   docker-compose -f docker-compose.prod.yml logs -f
   ```

### Using Docker Swarm

```bash
# Initialize swarm (if not already done)
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml food-receipt-bot

# List services
docker service ls

# View logs
docker service logs -f food-receipt-bot_telegram-bot
```

## Monitoring and Maintenance

### Health Checks

The container includes health checks that verify the bot can connect to Telegram:

```bash
# Check container health
docker-compose ps

# View health check logs
docker inspect --format='{{json .State.Health}}' food-receipt-bot
```

### Log Management

Logs are automatically rotated in production configuration:
- Maximum file size: 10MB
- Maximum files: 3
- Location: `./logs/` directory

```bash
# View recent logs
docker-compose logs --tail=100 telegram-bot

# Follow logs in real-time
docker-compose logs -f telegram-bot
```

### Resource Usage

Monitor resource usage:

```bash
# View resource usage
docker stats food-receipt-bot

# View detailed container info
docker inspect food-receipt-bot
```

## Troubleshooting

### Common Issues

1. **"Configuration file not found"**:
   - Make sure `.env` file exists and has correct values
   - Check environment variables are set

2. **"Bot token not found"**:
   - Verify `BOT_TOKEN` in `.env` file
   - Ensure no extra spaces or quotes

3. **"Permission denied" errors**:
   - Check file permissions: `chmod 644 .env`
   - Ensure Docker has access to the directory

4. **Container keeps restarting**:
   - Check logs: `docker-compose logs telegram-bot`
   - Verify bot token is valid
   - Check network connectivity

### Debug Mode

Enable debug logging:

```bash
# Set in .env file
LOG_LEVEL=DEBUG

# Or as environment variable
docker-compose up -e LOG_LEVEL=DEBUG
```

### Container Shell Access

Access the container for debugging:

```bash
# Get shell access
docker-compose exec telegram-bot bash

# Or if container is not running
docker run -it --rm food-receipt-bot bash
```

## Security Considerations

1. **Environment Variables**: Never commit `.env` files to version control
2. **Network Security**: The bot runs in an isolated Docker network
3. **User Permissions**: Container runs as non-root user
4. **Resource Limits**: Production config includes memory and CPU limits
5. **Log Security**: Ensure log files don't contain sensitive information

## Backup and Recovery

### Backup Configuration

```bash
# Backup environment file
cp .env .env.backup

# Backup entire configuration
tar -czf food-receipt-bot-backup.tar.gz .env docker-compose*.yml logs/
```

### Recovery

```bash
# Restore from backup
tar -xzf food-receipt-bot-backup.tar.gz

# Restart services
docker-compose up -d
```

## Updates

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up --build -d
```

### Update Dependencies

```bash
# Update base image and dependencies
docker-compose build --no-cache
docker-compose up -d
```

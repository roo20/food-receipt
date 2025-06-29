# Makefile for Food Receipt Bot

# Default environment
ENV ?= dev

# Docker compose files
COMPOSE_FILE_DEV = docker-compose.yml
COMPOSE_FILE_PROD = docker-compose.prod.yml

# Select compose file based on environment
ifeq ($(ENV),prod)
    COMPOSE_FILE = $(COMPOSE_FILE_PROD)
else
    COMPOSE_FILE = $(COMPOSE_FILE_DEV)
endif

.PHONY: help build up down restart logs shell test clean setup

help: ## Show this help message
	@echo "Food Receipt Bot - Docker Commands"
	@echo ""
	@echo "Usage: make [command] [ENV=dev|prod]"
	@echo ""
	@echo "Commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Initial setup - create .env file
	@if [ ! -f .env ]; then \
		cp .env.template .env; \
		echo "Created .env file from template"; \
		echo "Please edit .env file with your actual bot token and user ID"; \
	else \
		echo ".env file already exists"; \
	fi

build: ## Build the Docker image
	docker-compose -f $(COMPOSE_FILE) build

up: ## Start the bot (detached)
	docker-compose -f $(COMPOSE_FILE) up -d

up-fg: ## Start the bot (foreground)
	docker-compose -f $(COMPOSE_FILE) up

down: ## Stop and remove containers
	docker-compose -f $(COMPOSE_FILE) down

restart: ## Restart the bot
	docker-compose -f $(COMPOSE_FILE) restart

logs: ## Show logs (follow)
	docker-compose -f $(COMPOSE_FILE) logs -f telegram-bot

logs-tail: ## Show last 100 log lines
	docker-compose -f $(COMPOSE_FILE) logs --tail=100 telegram-bot

shell: ## Access container shell
	docker-compose -f $(COMPOSE_FILE) exec telegram-bot bash

status: ## Show container status
	docker-compose -f $(COMPOSE_FILE) ps

test: ## Run tests
	docker-compose -f $(COMPOSE_FILE) run --rm telegram-bot python test_receipt.py

clean: ## Remove containers, networks, and images
	docker-compose -f $(COMPOSE_FILE) down --rmi all --volumes --remove-orphans

clean-all: ## Remove everything including unused images and volumes
	docker system prune -a --volumes

deploy: setup build up ## Full deployment (setup + build + up)

redeploy: down build up ## Redeploy (down + build + up)

# Development specific commands
dev-setup: ENV=dev
dev-setup: setup ## Setup for development

dev-up: ENV=dev
dev-up: up ## Start development environment

dev-logs: ENV=dev
dev-logs: logs ## Show development logs

# Production specific commands  
prod-setup: ENV=prod
prod-setup: setup ## Setup for production

prod-deploy: ENV=prod
prod-deploy: deploy ## Deploy to production

prod-up: ENV=prod
prod-up: up ## Start production environment

prod-logs: ENV=prod
prod-logs: logs ## Show production logs

prod-restart: ENV=prod
prod-restart: restart ## Restart production environment

# Health and monitoring
health: ## Check container health
	@echo "Container Status:"
	@docker-compose -f $(COMPOSE_FILE) ps
	@echo ""
	@echo "Health Check:"
	@docker inspect --format='{{.State.Health.Status}}' $$(docker-compose -f $(COMPOSE_FILE) ps -q telegram-bot) 2>/dev/null || echo "Health check not available"

stats: ## Show container resource usage
	docker stats $$(docker-compose -f $(COMPOSE_FILE) ps -q) --no-stream

# Backup and maintenance
backup: ## Backup configuration
	@mkdir -p backups
	@tar -czf backups/config-backup-$$(date +%Y%m%d-%H%M%S).tar.gz .env docker-compose*.yml logs/ || true
	@echo "Backup created in backups/ directory"

update: ## Update and restart
	git pull
	make redeploy ENV=$(ENV)

# Examples
example-dev: ## Example: Start development environment
	@echo "Starting development environment..."
	make dev-setup
	make dev-up
	make dev-logs

example-prod: ## Example: Deploy to production
	@echo "Deploying to production..."
	make prod-setup
	make prod-deploy

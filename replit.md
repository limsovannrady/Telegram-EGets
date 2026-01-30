# Telegram Bot - Replit Agent Guide

## Overview

This is a Telegram bot application built with Python that monitors and processes messages. The bot includes functionality for copying codes via inline keyboard buttons and runs a health check HTTP server for deployment platforms like Render.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Components

**Bot Framework**
- Uses `python-telegram-bot` library for Telegram Bot API integration
- Implements async/await pattern for handling bot events
- Handles message copying functionality with inline keyboard buttons

**Health Check Server**
- Simple HTTP server running on a configurable port (default 5000)
- Responds with "OK" to GET requests for deployment health monitoring
- Runs in a separate thread to not block the main bot loop

**Message Handling**
- Uses callback query handlers for inline button interactions
- Implements scheduled message deletion via job queue
- Targets a specific group ID for message forwarding/processing

### Design Decisions

**Threading Model**
- Health check server runs in a separate thread
- Bot uses async event loop for Telegram API calls
- This separation ensures health checks don't interfere with bot operations

**Environment-Based Configuration**
- Bot token stored in `TELEGRAM_BOT_TOKEN` environment variable
- Target group ID configured via `TARGET_GROUP_ID` environment variable
- Port configuration via `PORT` environment variable (for deployment flexibility)

## External Dependencies

### Third-Party Services
- **Telegram Bot API**: Core messaging platform integration
- **Render** (or similar): Deployment platform requiring health check endpoint

### Python Packages
- `python-telegram-bot`: Telegram Bot API wrapper
- Standard library: `logging`, `os`, `re`, `threading`, `http.server`

### Environment Variables Required
| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Authentication token for Telegram Bot API |
| `TARGET_GROUP_ID` | Telegram group ID for message operations |
| `PORT` | HTTP server port for health checks (default: 5000) |
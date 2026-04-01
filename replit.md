# Telegram Bot - Replit Agent Guide

## Overview

This is a Telegram bot application built with Python that monitors and processes messages from Telegram groups/channels. The bot detects E-GetS verification codes and forwards them to a target group, with auto-deletion after 60 seconds.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Components

**Bot Framework**
- Uses `python-telegram-bot` library (v22+) for Telegram Bot API integration
- Implements async/await pattern for handling bot events
- Handles message copying functionality with inline keyboard buttons

**Health Check Server**
- Simple HTTP server running on port 5000 (configurable via `PORT` env var)
- Responds with "OK" to GET requests for deployment health monitoring
- Runs in a separate daemon thread so it doesn't block the main bot loop
- Keeps the process alive even when `TELEGRAM_BOT_TOKEN` is not set

**Message Handling**
- Uses callback query handlers for inline button interactions
- Implements scheduled message deletion via job queue (60 second delay)
- Targets a specific group ID for message forwarding/processing
- Monitors for E-GetS verification code messages

### Design Decisions

**Threading Model**
- Health check server runs in a separate daemon thread
- Bot uses async event loop for Telegram API calls
- This separation ensures health checks don't interfere with bot operations

**Graceful Degradation**
- If `TELEGRAM_BOT_TOKEN` is not set, the health server still runs and the process stays alive
- This allows the workflow to start successfully even without credentials configured

**Environment-Based Configuration**
- Bot token stored in `TELEGRAM_BOT_TOKEN` environment variable
- Target group ID configured via `TARGET_GROUP_ID` environment variable
- Port configuration via `PORT` environment variable (default: 5000)

## External Dependencies

### Third-Party Services
- **Telegram Bot API**: Core messaging platform integration

### Python Packages
- `python-telegram-bot[job-queue]`: Telegram Bot API wrapper with scheduling support
- Standard library: `logging`, `os`, `re`, `threading`, `http.server`, `time`

### Environment Variables Required
| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Authentication token for Telegram Bot API |
| `TARGET_GROUP_ID` | Telegram group ID for message operations |
| `PORT` | HTTP server port for health checks (default: 5000) |

## Setup Notes

- Python 3.11 runtime (Replit) / Python 3.12 (Vercel)
- Dependencies managed via `uv` / `pyproject.toml` (Replit) and `requirements.txt` (Vercel)
- The bare `telegram` package (0.0.1) conflicts with `python-telegram-bot` — do not add it as a dependency
- Workflow: "Start application" runs `python main.py` on port 5000 (polling mode for Replit dev)
- Deployment target: VM (always-running, needed for long-lived bot polling)

## Vercel Webhook Deployment

The project supports Vercel serverless webhook deployment in addition to Replit polling mode.

### Files
- `api/webhook.py` — Vercel serverless function, handles POST updates from Telegram
- `requirements.txt` — Python dependencies for Vercel
- `vercel.json` — Vercel function config (Python 3.12, 10s max duration)

### Steps to deploy on Vercel
1. Push this repo to GitHub
2. Import into Vercel and set environment variables:
   - `TELEGRAM_BOT_TOKEN`
   - `TARGET_GROUP_ID`
3. Deploy — your webhook URL will be `https://<your-domain>/api/webhook`
4. Register the webhook with Telegram:
   ```
   https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<your-domain>/api/webhook
   ```

### Note on job_queue / auto-delete
The 60-second message auto-deletion feature (job_queue) is **not available** in Vercel serverless mode because functions terminate after handling each request. The core forwarding of verification codes works fully.

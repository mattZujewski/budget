# Running Budget App in Docker

This guide explains how to run the Budget application using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose installed on your system

## Setup

1. Make sure your `.env` file is configured with the appropriate settings:
   ```
   # Budget App Configuration
   LOG_LEVEL=INFO
   
   # AI API Provider (none, claude, openai, local)
   AI_PROVIDER=none
   
   # Claude API Settings
   CLAUDE_ENABLED=False
   CLAUDE_API_KEY=your_api_key_here
   ```

2. Build the Docker image:
   ```bash
   docker-compose build
   ```

## Running the Application

### Using Docker Compose

The `docker-compose.yml` file provides a convenient way to run the application with predefined settings.

1. Run the default command (check AI config status):
   ```bash
   docker-compose up
   ```

2. Run a specific command by overriding the default:
   ```bash
   docker-compose run --rm budget import /app/data/mystatement.csv --source "My Bank"
   ```

3. Run the AI assistant:
   ```bash
   docker-compose run --rm budget assistant "How much did I spend on groceries last month?"
   ```

### Using Docker Directly

You can also run the Docker container directly without Docker Compose:

1. Build the image:
   ```bash
   docker build -t budget-app .
   ```

2. Run a command:
   ```bash
   docker run --rm -v $(pwd)/data:/app/data -v $(pwd)/logs:/app/logs -v $(pwd)/.env:/app/.env budget-app ai-config --status
   ```

3. Import transactions:
   ```bash
   docker run --rm -v $(pwd)/data:/app/data -v $(pwd)/logs:/app/logs -v $(pwd)/.env:/app/.env budget-app import /app/data/mystatement.csv --source "My Bank"
   ```

## Data Persistence

The Docker setup maps the following directories from your host to the container:

- `./data:/app/data` - Stores your transaction data and ML models
- `./logs:/app/logs` - Stores application logs
- `./.env:/app/.env` - Your configuration file

This ensures that your data persists between container runs.

## Troubleshooting

1. **File permissions**: If you encounter permission issues, ensure the mounted directories have appropriate permissions:
   ```bash
   chmod -R 777 data logs
   ```

2. **Missing dependencies**: If additional Python packages are needed, add them to `requirements.txt` and rebuild the image:
   ```bash
   docker-compose build
   ```

3. **Command not found**: If a command doesn't work, check that it's defined in `main.py` and that you're using the correct syntax.
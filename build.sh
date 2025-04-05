#!/bin/bash

# Build and run script for Budget Application Docker Container

# Exit on any error
set -e

# Color codes for console output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${GREEN}✔ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✘ $1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_warning "Docker Compose not found. Trying with 'docker compose'."
    DOCKER_COMPOSE_CMD="docker compose"
else
    DOCKER_COMPOSE_CMD="docker-compose"
fi

# Ensure .env file exists
if [ ! -f .env ]; then
    print_warning "No .env file found. Creating a default .env file."
    cp .env.example .env
fi

# Build options
BUILD_OPTS=""
COMMAND=""

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -b|--build) BUILD_OPTS="--build"; shift ;;
        -d|--debug) COMMAND="debug"; shift ;;
        -a|--assistant) COMMAND="assistant"; shift ;;
        -i|--import) 
            COMMAND="import"
            shift
            if [[ "$1" ]]; then
                IMPORT_FILE="$1"
                shift
            fi
            ;;
        *) 
            print_error "Unknown parameter passed: $1"
            exit 1
            ;;
    esac
done

# Build the Docker image
print_status "Building Docker image..."
$DOCKER_COMPOSE_CMD build $BUILD_OPTS

# Run based on command
if [ "$COMMAND" == "debug" ]; then
    print_status "Running application debug script..."
    $DOCKER_COMPOSE_CMD run --rm budget debug.py
elif [ "$COMMAND" == "assistant" ]; then
    print_status "Starting AI Financial Assistant..."
    $DOCKER_COMPOSE_CMD run --rm budget assistant "Provide an overview of my financial situation"
elif [ "$COMMAND" == "import" ]; then
    if [ -z "$IMPORT_FILE" ]; then
        print_error "Import file not specified. Use -i /path/to/statement.csv"
        exit 1
    fi
    print_status "Importing transactions from $IMPORT_FILE..."
    $DOCKER_COMPOSE_CMD run --rm -v "$(pwd)/$IMPORT_FILE:/app/data/import_statement.csv" budget import /app/data/import_statement.csv
else
    # Default: run debug script
    print_status "Running default debug script..."
    $DOCKER_COMPOSE_CMD run --rm budget
fi

print_status "Docker operation completed successfully!"
# List all recipes
help:
  @just -l

[group: "Initialize project"]
init:
  @uv sync

# Run capstone project with Docker
[group: "App"]
up-build:
  @docker compose -f ./docker-compose.yml up --build -w

# Stop App docker containers
[group: "App"]
down:
  @docker compose -f ./docker-compose.yml down

# Stop App docker containers and remove volumes
[group: "Clean up"]
down-clean:
  @docker compose -f ./docker-compose.yml down && \
    echo "🔄 Deleting all unused volumes..." && \
    docker volume prune -af

# Lint
[group: "Format"]
lint:
  @uv run ruff check .

# Format
[group: "Format"]
format:
  @uv run ruff format .

# Start Ollama
[group: "Ollama"]
up-ollama:
  @chmod +x ./scripts/start-ollama.sh
  @bash ./scripts/start-ollama.sh

# Stop Ollama
[group: "Ollama"]
down-ollama:
  @chmod +x ./scripts/stop-ollama.sh
  @bash ./scripts/stop-ollama.sh
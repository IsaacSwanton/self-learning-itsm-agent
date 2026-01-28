# Running with Podman/Docker

This project is designed to run in containers for better isolation and reproducibility.

## Prerequisites

- [Podman](https://podman.io/) or Docker installed
- For Podman on Windows, you may need [WSL 2](https://docs.microsoft.com/en-us/windows/wsl/install) or [Podman Desktop](https://podman.io/docs/installation#windows)

## Quick Start

### Option 1: Using Podman Compose (Recommended)

```powershell
# Start all services (Ollama + Backend)
podman-compose up --build

# In another terminal, the services will be available at:
# - Frontend: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Ollama: http://localhost:11434
```

### Option 2: Using Docker Compose

If you have Docker installed instead of Podman:

```powershell
docker-compose up --build
```

### Option 3: Manual Podman Commands

```powershell
# Start Ollama container
podman run -d -p 11434:11434 --name itsm-ollama ollama/ollama

# Pull a model (one-time setup)
podman exec itsm-ollama ollama pull llama3.2:3b

# Build and run the backend
podman build -t itsm-backend .
podman run -p 8000:8000 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -e OLLAMA_MODEL=llama3.2:3b \
  -v ./data:/app/data \
  -v ./backend:/app/backend \
  itsm-backend
```

## Stopping Services

```powershell
# Stop all services
podman-compose down

# Or with Docker
docker-compose down
```

## Viewing Logs

```powershell
# View all logs
podman-compose logs -f

# View specific service logs
podman-compose logs -f ollama
podman-compose logs -f backend
```

## Configuration

You can customize behavior by editing `docker-compose.yml`:

- `OLLAMA_MODEL`: Change the LLM model (e.g., `llama2`, `neural-chat`, `mistral`)
- `PORT`: Change the backend port
- `OLLAMA_BASE_URL`: Adjust if running Ollama separately

## First Run Setup

The first time you run the containers:

1. Ollama will start and download the model (~4GB for llama3.2:3b)
2. Backend will wait for Ollama to be healthy before starting
3. Once ready, the service will be available at http://localhost:8000

This may take 5-10 minutes on first run depending on your internet speed.

## Common Issues

**Port already in use:**
```powershell
# Find what's using the port
netstat -ano | findstr :8000

# Either stop that service or change ports in docker-compose.yml
```

**Ollama model download fails:**
```powershell
# Check Ollama logs
podman-compose logs ollama

# You can manually pull the model in the container
podman exec itsm-ollama ollama pull llama3.2:3b
```

**Out of disk space:**
```powershell
# Clean up unused containers/images
podman system prune -a

# Or just clean containers
podman-compose down -v  # -v removes volumes too
```

## Development Workflow

With `docker-compose.yml` configured for development:
- Changes to `backend/` code are live-reloaded
- Changes to `data/` persist across restarts
- API is available at http://localhost:8000/docs for testing

## Scaling for Production

For production deployments:
1. Remove `--reload` from the backend command
2. Use a proper reverse proxy (nginx) in front
3. Add SSL/TLS certificates
4. Use managed Ollama instance or separate GPU container
5. Set up proper logging and monitoring

# 🐳 Container Setup for ITSM Agent

## Why Containers?
✅ Ollama (large models) isolated from your system  
✅ Same environment everywhere (dev, test, prod)  
✅ Easy to manage dependencies  
✅ Fast to rebuild and reset  
✅ Production-ready setup  

## Quick Start (5 minutes)

### Step 1: Install Podman
[Download Podman for Windows](https://podman.io/docs/installation#windows)

On Windows, you have two options:
- **Podman Desktop** (GUI, recommended for beginners) - includes Podman
- **WSL 2 + Podman** (CLI, for advanced users)

Verify installation:
```powershell
podman --version
```

### Step 2: Start the Containers
```powershell
cd c:\Projects\self-learning-itsm-agent

# Option A: Using the helper script (easiest)
.\manage-containers.ps1 start

# Option B: Manual command
podman-compose up -d --build
```

### Step 3: Wait for Ollama (first run takes 5-10 minutes)
```powershell
# Monitor progress
.\manage-containers.ps1 logs

# Or check status
.\manage-containers.ps1 status
```

### Step 4: Access the Application
- **Frontend:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Ollama API:** http://localhost:11434

## Common Commands

```powershell
# Start everything
.\manage-containers.ps1 start

# View logs in real-time
.\manage-containers.ps1 logs

# Stop everything
.\manage-containers.ps1 stop

# Restart (after code changes)
.\manage-containers.ps1 restart

# Test connectivity
.\manage-containers.ps1 test

# Full rebuild
.\manage-containers.ps1 rebuild

# Clean up everything
.\manage-containers.ps1 clean
```

## What's Running?

| Service | Port | Purpose |
|---------|------|---------|
| **Ollama** | 11434 | Local LLM inference engine |
| **Backend** | 8000 | FastAPI server |
| **Frontend** | 8000 | Web dashboard (served by backend) |

## First Run Notes

1. **Model Download**: First time Ollama starts, it downloads the model (~4GB)
   - This is normal and happens only once
   - Check `podman-compose logs ollama` to see progress

2. **Backend Wait**: Backend waits for Ollama to be ready
   - Once Ollama is healthy, backend auto-starts

3. **Development Mode**: Code changes auto-reload
   - Edit files in `backend/` or `frontend/` and refresh browser

## Troubleshooting

**Services won't start:**
```powershell
# Check logs
.\manage-containers.ps1 logs

# Rebuild everything
.\manage-containers.ps1 rebuild
```

**Port 8000 already in use:**
```powershell
# Find what's using it
netstat -ano | findstr :8000

# Kill the process (if safe) or edit docker-compose.yml to use different port
```

**Out of disk space:**
```powershell
# Clean unused images/containers
.\manage-containers.ps1 clean
```

**Ollama is slow:**
- First request is slow (model loads into memory)
- Subsequent requests are fast
- Consider the `ollama pull` output during startup

## Next Steps

1. ✅ Run `.\manage-containers.ps1 start`
2. ✅ Open http://localhost:8000/docs
3. ✅ Try the `/api/tickets/process` endpoint
4. ✅ View real-time logs: `.\manage-containers.ps1 logs`

## Production Deployment

For production on a server:
1. Use cloud-hosted Ollama instead of local
2. Add SSL/TLS certificates
3. Use a reverse proxy (nginx)
4. Configure proper resource limits in docker-compose.yml
5. Set up monitoring and logging
6. Use environment-specific .env files

See `PODMAN_SETUP.md` for advanced configurations.

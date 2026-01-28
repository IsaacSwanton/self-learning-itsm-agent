"""
ITSM Learning Agent - FastAPI Backend

Main application entry point with static file serving for the frontend.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .routers import tickets, skills
from .services.ollama_client import ollama_client
from .config import HOST, PORT

app = FastAPI(
    title="ITSM Learning Agent",
    description="A self-improving IT Service Management agent using Claude Skills architecture",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tickets.router)
app.include_router(skills.router)

# Serve frontend
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@app.get("/")
async def serve_frontend():
    """Serve the main frontend HTML"""
    return FileResponse(FRONTEND_DIR / "index.html")


# Mount static files
if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    ollama_available = await ollama_client.check_connection()
    return {
        "status": "healthy",
        "ollama_available": ollama_available,
        "message": "Ollama is running" if ollama_available else "Ollama not available - make sure it's running"
    }


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    await ollama_client.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)

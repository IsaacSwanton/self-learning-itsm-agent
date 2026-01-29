import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
SKILLS_DIR = BASE_DIR / ".agent" / "skills"
DATA_DIR = BASE_DIR / "data"
TICKETS_DIR = DATA_DIR / "tickets"
PROPOSED_SKILLS_DIR = DATA_DIR / "proposed_skills"
REPORTS_DIR = DATA_DIR / "reports"

# Ensure directories exist
for dir_path in [SKILLS_DIR, TICKETS_DIR, PROPOSED_SKILLS_DIR, REPORTS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

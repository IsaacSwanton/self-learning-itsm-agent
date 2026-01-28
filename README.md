# Self Learning ITSM Agent

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)

A **self-improving IT Service Management agent** that uses a modular skills architecture to learn from historical ticket data and proposes new skills for human approval.

## ✨ Features

- **🎫 Ticket Processing** - Parse, categorize, route, and suggest resolutions for ITSM tickets
- **📚 Skills Architecture** - Modular skills in Markdown format for easy customization
- **🧠 Learning Loop** - Automatically proposes new skills when it identifies patterns
- **👤 Human-in-the-Loop** - Review and approve proposed skills before deployment
- **🖥️ Web Dashboard** - Real-time ticket processing and skills management UI

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai) installed and running
- A model pulled (e.g., `ollama pull llama3.2:3b`)

### Installation

```bash
# Clone the repository
git clone https://github.com/isaacswanton-777/self-learning-itsm-agent.git
cd self-learning-itsm-agent

# Create virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Running

```bash
# Start the backend server
python backend/main.py

# Open the UI in your browser
# Navigate to http://localhost:8000
```

## 📁 Project Structure

```
self-learning-itsm-agent/
├── .agent/skills/        # Agent Skills (SKILL.md files)
│   ├── categorization/   # Ticket categorization skill
│   ├── resolution/       # Resolution suggestion skill
│   ├── routing/          # Ticket routing skill
│   └── ticket-parser/    # Ticket parsing skill
├── backend/              # FastAPI backend
│   ├── main.py           # Application entry point
│   ├── models.py         # Pydantic models
│   ├── routers/          # API routes
│   └── services/         # Business logic
├── frontend/             # Web UI
│   ├── index.html        # Main dashboard
│   ├── css/              # Stylesheets
│   └── js/               # JavaScript
└── data/                 # Data storage
    ├── sample_tickets.json
    ├── proposed_skills/  # Runtime-generated skill proposals
    └── reports/          # Processing reports
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/tickets/process` | Process a single ticket |
| `GET` | `/api/skills` | List all available skills |
| `GET` | `/api/skills/proposed` | List proposed skills pending approval |
| `POST` | `/api/skills/approve/{id}` | Approve a proposed skill |
| `DELETE` | `/api/skills/proposed/{id}` | Reject a proposed skill |

## 🧠 How Learning Works

1. **Process Tickets** - The agent processes incoming ITSM tickets using existing skills
2. **Detect Patterns** - When the agent encounters repeated failures or new patterns, it identifies learning opportunities
3. **Propose Skills** - New skill proposals are generated and saved for review
4. **Human Review** - Administrators review and approve/reject proposed skills
5. **Deploy** - Approved skills are added to the active skill set

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Ollama](https://ollama.ai) for local LLM inference

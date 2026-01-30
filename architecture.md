flowchart TD
    subgraph UI["User Interface"]
        A["Browser - Frontend"]
    end

    subgraph Backend["Backend Server (FastAPI)"]
        B["API Endpoints"]
        C["Ticket Processor Service"]
        D["Learning Engine Service"]
        E["Skill Loader Service"]
    end

    subgraph Intelligence["Intelligence Core"]
        F["Ollama LLM - llama3.2:3b"]
    end

    subgraph Storage["Data Storage (File System)"]
        G["Uploaded Tickets<br/>(e.g., sample_tickets.json)"]
        H["Core Skills<br/>(/backend/skills/)"]
        I["Learned Skills<br/>(/data/proposed_skills/approved_*.md)"]
        J["Proposed Skills<br/>(/data/proposed_skills/pending_*.json)"]
        K["Processing Results<br/>(/data/tickets/run-*.json)"]
    end

    %% Interactions
    User -->|"Interacts with"| A
    A -->|"1. Upload Tickets (JSON/CSV)"| B
    B -->|"2. Process Tickets Request"| C
    C -->|"3. Get Skills"| E
    E -->|"4. Load Core Skills"| H
    E -->|"5. Load Learned Skills"| I
    C -->|"6. Build System Prompt"| F
    C -->|"7. Process Ticket Data"| G
    C -->|"8. Get Prediction"| F
    C -->|"9a. On Success: Store Results"| K
    C -->|"9b. On Failure: Trigger Learning"| D
    D -->|"10. Analyze Failure & Propose Skill"| F
    D -->|"11. Save Proposed Skill"| J
    A -->|"12. View Skills"| B
    B -->|"13. Get Active Skills"| E
    B -->|"14. Get Proposed Skills"| D
    A -->|"15. Approve Skill"| B
    B -->|"16. Approve Skill"| D
    D -->|"17. Convert to Learned Skill"| I
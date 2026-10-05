# ScholarPulse

**ScholarPulse** is an AI-powered research assistant designed to help researchers discover, organize, analyze, compare, and interact with academic papers.

The project evolved through multiple research-assistant prototypes, beginning with an initial AI research assistant and progressing through Gemini, Groq/Llama, Streamlit, and Lumora-based versions before becoming the current **ScholarPulse** application.

## Current Version

**V7.0 — ScholarPulse**

Current architecture:

* **Frontend:** React + Vite
* **Backend:** FastAPI
* **Authentication:** JWT
* **Database:** SQLite
* **Research pipeline:** paper search, retrieval, processing, embeddings, clustering, and summaries
* **Paper interaction:** reader, library, comparison, citations, and Paper Chat UI

---

## Features

### Authentication

* User registration
* User login
* JWT-based authentication
* Protected application routes
* Session persistence
* Logout

### Research

* Search for research papers
* View research history
* Restore previous research results
* Open individual papers
* Navigate between research results and paper reader

### Paper Library

* Save papers to a personal library
* Remove papers from the library
* Search saved papers
* Open saved papers in the paper reader

### Paper Reader

* View paper information
* Open available PDF documents
* Copy citations
* Navigate directly from research results or the library

### Paper Comparison

* Select and compare papers
* View paper comparison information
* Navigate from comparison results to individual papers

### Paper Chat

* Paper Chat interface for interacting with research papers
* UI prepared for future multi-model / RAG-based research conversations

> AI-generated responses and multi-model paper chat are currently deferred while the core application architecture is being stabilized.

---

## Architecture

```text
ScholarPulse
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── data/
│   │   └── pages/
│   ├── App.jsx
│   ├── main.jsx
│   ├── index.css
│   ├── package.json
│   └── vite.config.js
│
└── backend/
    ├── src/
    │   ├── api/
    │   │   ├── auth.py
    │   │   ├── paper.py
    │   │   └── research.py
    │   ├── services/
    │   │   └── research_service.py
    │   ├── utils/
    │   │   ├── auth.py
    │   │   └── utility.py
    │   ├── app.py
    │   ├── clustering.py
    │   ├── config.py
    │   ├── database.py
    │   ├── embedding_utils.py
    │   ├── fetchers.py
    │   └── summarizer.py
    │
    ├── requirements.txt
    └── .env.example
```

---

## Running the Project Locally

### Prerequisites

Make sure you have:

* Python 3.x
* Node.js and npm
* Git

### 1. Clone the repository

```bash
git clone https://github.com/saumya-2409/scholarpulse.git
cd scholarpulse
```

### 2. Backend setup

Navigate to the backend:

```powershell
cd backend
```

Create and activate a virtual environment if needed:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create the environment file:

```powershell
Copy-Item .env.example .env
```

Start the FastAPI server:

```powershell
python -m uvicorn app:app --reload --app-dir src
```

The backend will run at:

```text
http://127.0.0.1:8000
```

API health check:

```text
http://127.0.0.1:8000/health
```

### 3. Frontend setup

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

The frontend will run at:

```text
http://localhost:5173
```

---

## Environment Variables

Backend environment variables are documented in:

```text
backend/.env.example
```

The project supports optional configuration for authentication and research/LLM providers, including:

```text
JWT_SECRET_KEY

GROQ_API_KEY
OPENAI_API_KEY
ANTHROPIC_API_KEY
COHERE_API_KEY
MISTRAL_API_KEY
TOGETHER_API_KEY
GEMINI_API_KEY
LLAMA_API_KEY

SEMANTIC_SCHOLAR_API_KEY
```

API keys should **never** be committed to Git.

---

## Development Status

The current ScholarPulse application has been tested across the core application flow:

* Registration
* Login
* Logout
* Protected routes
* Session persistence
* Research/search
* Research history
* Restoring previous research
* Paper opening
* Saving papers
* Removing papers from the library
* Library search
* Paper reader
* Citation copying
* PDF opening
* Paper comparison
* Navigation between research, library, comparison, and reader
* Paper Chat UI
* Frontend production build
* Backend startup and health checks

### Currently Deferred

The following are intentionally not part of the current completed functionality:

* Actual LLM-generated Paper Chat responses
* Gemini/API-key integration
* API quota and rate-limit handling
* Multi-model chat execution
* AI-generated comparison synthesis

These can be implemented as future iterations without changing the historical versions preserved in this repository.

---

# Project Evolution

ScholarPulse is the result of several iterations of the research assistant project.

| Version | Branch                 | Tag                 | Description                          |
| ------- | ---------------------- | ------------------- | ------------------------------------ |
| V1      | `history/v1-initial`   | `v1.0`              | Initial AI Research Assistant        |
| V2      | `history/v2-mvp`       | `v2.0`              | Research Assistant MVP               |
| V3      | `history/v3-gemini`    | `v3.0-gemini`       | Gemini-based version                 |
| V4      | `history/v4-groq`      | `v4.0-groq`         | Groq / Llama version                 |
| V5      | `history/v5-streamlit` | `v5.0-streamlit`    | Streamlit research assistant         |
| V6      | `history/v6-lumora`    | `v6.0-lumora`       | Lumora research assistant            |
| V7      | `main`                 | `v7.0-scholarpulse` | Current React + FastAPI ScholarPulse |

Historical implementations are preserved in dedicated branches and version tags rather than being merged into the current `main` branch.

---

## Repository Structure

### `main`

Contains the current ScholarPulse application.

### `history/*`

Contains preserved historical implementations:

```text
history/v1-initial
history/v2-mvp
history/v3-gemini
history/v4-groq
history/v5-streamlit
history/v6-lumora
```

### Version Tags

```text
v1.0
v2.0
v3.0-gemini
v4.0-groq
v5.0-streamlit
v6.0-lumora
v7.0-scholarpulse
```

This structure makes it possible to inspect the evolution of the project without rewriting or merging unrelated historical implementations into the current application.

---

## Future Directions

Potential future development includes:

* RAG-based Paper Chat
* Multi-model research conversations
* AI-generated paper comparisons
* Improved research summarization
* More research-paper sources
* Advanced paper clustering
* Citation and bibliography management
* More robust research history
* Production deployment
* Improved testing and observability

---

## License

This project is currently maintained as a personal research and portfolio project.

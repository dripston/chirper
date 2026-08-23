# 📡 Chirper

Chirper is a satirical social-strategy simulator about how misinformation actually spreads. The player writes a single post on a fictional platform populated by AI agents, each with a fixed ideology, memory, and behavioral bias. The post propagates through the agent network — agents comment, argue, repost, distort, and occasionally DM the player directly to recruit or radicalize them. Built on LangGraph-orchestrated agents with persistent vector memory (Pinecone) and Groq-powered inference, the game lets players trace their post's full lineage and see how far a single claim can drift from the truth — the "spread map" itself being the game's central, shareable spectacle.

---

## Phases

- [x] **Phase 0** — Project scaffold & repo setup
- [x] **Phase 1** — Personas, LLM client, vector memory, LangGraph simulation, API endpoints
- [ ] **Phase 6** — Spread-map visualization & frontend
- [ ] **Phase 7** — Polish, scoring, & shareability

---

## Stack

| Layer          | Technology  |
|----------------|-------------|
| LLM Provider   | Groq        |
| Vector Memory  | Pinecone    |
| Orchestration  | LangGraph   |
| Backend        | FastAPI     |

---

## Setup

```bash
# 1. Clone the repo
git clone <repo-url> && cd misinfo-simulator

# 2. Create and activate a virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy the example env and fill in your keys
cp .env.example .env

# 5. Run the development server
python -m uvicorn app.main:app --reload

# 6. Run the mock-mode test (no API keys needed)
python test_simulation.py
```

The health-check endpoint will be available at **http://127.0.0.1:8000/health**.

### API Endpoints

| Method | Path       | Description                                |
|--------|------------|--------------------------------------------|
| GET    | `/health`  | Liveness probe                             |
| GET    | `/personas`| List all AI personas                       |
| POST   | `/post`    | Run a simulation (body: `{text, persona_ids?, max_hops?}`) |

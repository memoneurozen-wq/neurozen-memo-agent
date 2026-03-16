# 🧠 NeuroZen Memo Agent

AI sales agent with long-term memory using Pinecone vector database, LangChain, Groq and FastAPI — deployed on Render.

Built as part of the **Código Fluente** course on multi-agent AI systems.

---

## 📖 About

This project evolves the basic sales agent from the previous lesson by adding **persistent long-term memory**. The agent — named **Memo** — remembers each visitor's name, interests, and previous questions across sessions, even after the browser is closed.

Memory is stored as vector embeddings in **Pinecone** (cloud), retrieved via semantic search, and injected into the LLM prompt before each response. The backend runs on **FastAPI** hosted on **Render**, making the project fully accessible via a public URL.

---

## 🏗️ Architecture

```
Browser (index.html)
    ↓ fetch POST /chat
FastAPI Server (Render)
    ↓ retrieve memories
Pinecone (vector store)
    ↓ inject context into prompt
Groq API (LLM - llama3-70b)
    ↓ response
Browser
    ↑ save interaction
Pinecone
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq (llama3-70b-8192) |
| Vector store | Pinecone (serverless, free tier) |
| Embeddings | Sentence Transformers (all-MiniLM-L6-v2) |
| Backend | FastAPI + Uvicorn |
| Hosting | Render (free tier) |
| Orchestration | LangChain |
| Frontend | HTML + CSS + Vanilla JS |

---

## 📁 Project Structure

```
neurozen-memo-agent/
├── memory_agent.py       # Agent core: AgentMemory + NeuroZenAgent classes
├── server.py             # FastAPI REST API
├── test_memory.py        # Memory persistence and isolation tests
├── inspect_db.py         # Pinecone inspection utility
├── requirements.txt      # Python dependencies
└── js/
    ├── agent.js          # Prompt compatibility stub
    ├── chat.js           # API communication + chat UI logic
    ├── ui.js             # Message rendering
    └── form.js           # Email capture → Google Sheets
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- [Groq API key](https://console.groq.com/)
- [Pinecone API key](https://app.pinecone.io/)
- [Render account](https://render.com/) (free, no credit card required)

### Local setup

```bash
# Clone the repository
git clone https://github.com/your-username/neurozen-memo-agent.git
cd neurozen-memo-agent

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Configure API keys

Open `memory_agent.py` and replace the placeholder values:

```python
GROQ_API_KEY     = "your-groq-api-key"
PINECONE_API_KEY = "your-pinecone-api-key"
PINECONE_REGION  = "us-east-1"  # check your Pinecone dashboard
```

### Run tests locally

```bash
python test_memory.py
```

Expected output on the second session: the agent should reference information from the first session without being told again.

### Run the server locally

```bash
uvicorn server:app --reload
```

API docs available at `http://localhost:8000/docs`

---

## ☁️ Deploy to Render

1. Push the project to GitHub
2. Create a new **Web Service** on Render connected to your repo
3. Set the following:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - **Instance type:** Free
4. Add environment variables:
   - `GROQ_API_KEY`
   - `PINECONE_API_KEY`
5. Update `memory_agent.py` to read keys from environment:
   ```python
   import os
   GROQ_API_KEY     = os.environ.get("GROQ_API_KEY", "")
   PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY", "")
   ```
6. Update `API_URL` in `js/chat.js` with your Render URL:
   ```javascript
   const API_URL = "https://your-service-name.onrender.com";
   ```

---

## 🧪 Key Concepts Demonstrated

**Long-term memory with RAG** — interactions are saved as vector embeddings and retrieved by semantic similarity, not keyword matching.

**Session isolation** — each user has a unique `session_id` stored in `localStorage`. Pinecone filters memories by this ID, so users never see each other's data.

**Short-term memory (sliding window)** — recent messages are kept in context up to a configurable limit, preventing prompt overflow.

**Dynamic prompt injection** — retrieved memories and user profile are formatted and injected into the system prompt before each LLM call.

---

## 📚 Course

This project is part of the **Código Fluente** course on multi-agent AI systems.

- 🌐 [codigofluente.com.br](https://www.codigofluente.com.br)
- 📺 YouTube: Código Fluente

---

## 📄 License

MIT
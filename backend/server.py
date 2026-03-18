import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from memory_agent import NeuroZenAgent

app = FastAPI(title="NeuroZen Agent API")

# Necessário para o frontend HTML conseguir chamar a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uma única instância do agente compartilhada entre todas as requisições
# Agora com fastembed, ele carrega rápido o suficiente para evitar timeout no Render
agent = NeuroZenAgent()


class ChatRequest(BaseModel):
    session_id: str
    message: str
    user_name: str | None = None


class ChatResponse(BaseModel):
    response: str
    memories_retrieved: int


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    metadata = {}
    if request.user_name:
        metadata["user_name"] = request.user_name

    memories = agent.memory.retrieve_memories(request.session_id, request.message)

    response = agent.chat(
        session_id=request.session_id,
        user_message=request.message,
        user_metadata=metadata if metadata else None
    )

    return ChatResponse(
        response=response,
        memories_retrieved=len(memories)
    )


@app.get("/profile/{session_id}")
async def get_profile(session_id: str):
    """Retorna o perfil acumulado de um usuário."""
    return agent.memory.get_user_profile(session_id)


@app.delete("/memory/{session_id}")
async def clear_memory(session_id: str):
    """Remove todas as memórias de um usuário."""
    agent.memory.clear_user_memory(session_id)
    return {"message": f"Memórias do usuário {session_id} removidas."}


@app.get("/")
async def root():
    """Health check — o Render usa este endpoint para verificar se o serviço está vivo."""
    return {"status": "ok", "agent": "Memo - NeuroZen"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
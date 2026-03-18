import os
from fastapi import FastAPI, BackgroundTasks
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
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    metadata = {}
    if request.user_name:
        metadata["user_name"] = request.user_name

    # Recuperação é rápida, mas necessária antes da resposta para injetar contexto
    memories = agent.memory.retrieve_memories(request.session_id, request.message)

    # Gera a resposta do Llama (isso leva alguns segundos e é a parte que o usuário aguarda)
    response = agent.generate_response(
        session_id=request.session_id,
        user_message=request.message
    )

    # AGENDA o salvamento no Pinecone para rodar depois que a resposta for enviada
    # Isso remove ~1 a 2 segundos de espera do usuário
    background_tasks.add_task(
        agent.memory.save_memory,
        session_id=request.session_id,
        user_message=request.message,
        agent_response=response,
        metadata=metadata if metadata else None
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
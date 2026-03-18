import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# Importamos a classe, mas não instanciamos ainda para evitar timeout no boot
from memory_agent import NeuroZenAgent

# Garante que os logs apareçam no Render sem atraso
print("🚀 Servidor NeuroZen iniciando...", flush=True)

app = FastAPI(title="NeuroZen Agent API")

# Necessário para o frontend HTML conseguir chamar a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instância global iniciada como None
agent_instance = None

def get_agent():
    """Retorna a instância do agente, carregando-a apenas se necessário."""
    global agent_instance
    if agent_instance is None:
        print("🧠 Carregando NeuroZenAgent e modelos de IA (Lazy Loading)...", flush=True)
        try:
            agent_instance = NeuroZenAgent()
            print("✅ Agente carregado com sucesso!", flush=True)
        except Exception as e:
            print(f"❌ ERRO CRÍTICO ao carregar o agente: {e}", flush=True)
            raise e
    return agent_instance


class ChatRequest(BaseModel):
    session_id: str
    message: str
    user_name: str | None = None


class ChatResponse(BaseModel):
    response: str
    memories_retrieved: int


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Obtém o agente (carrega agora se for a primeira vez)
    agent = get_agent()

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
    agent = get_agent()
    return agent.memory.get_user_profile(session_id)


@app.delete("/memory/{session_id}")
async def clear_memory(session_id: str):
    """Remove todas as memórias de um usuário."""
    agent = get_agent()
    agent.memory.clear_user_memory(session_id)
    return {"message": f"Memórias do usuário {session_id} removidas."}


@app.get("/")
async def root():
    """Health check — o Render usa este endpoint para verificar se o serviço está vivo."""
    return {
        "status": "ok", 
        "agent": "Memo - NeuroZen", 
        "ready": agent_instance is not None
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
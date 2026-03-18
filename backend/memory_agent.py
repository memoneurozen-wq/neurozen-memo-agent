from groq import Groq
from pinecone import Pinecone, ServerlessSpec
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv
from fastembed import TextEmbedding # Adicionado para funcionar com o código abaixo

# Carrega o arquivo .env do diretório raiz
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Silenciar avisos do HF Hub se o token não for fornecido
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# =============================================================
# CONFIGURAÇÃO
# =============================================================

GROQ_API_KEY     = os.environ.get("GROQ_API_KEY")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")

# Nome do index no Pinecone — será criado automaticamente se não existir
PINECONE_INDEX_NAME = "neurozen-memories"

# Região do seu projeto Pinecone (aparece na tela de API Keys)
PINECONE_REGION = "us-east-1"

# Modelo de embeddings — muito mais leve, sem Torch
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Quantos fragmentos de memória recuperar por consulta
TOP_K_MEMORIES = 3

# Quantas mensagens recentes manter no contexto direto
RECENT_HISTORY_SIZE = 6

# Prompt base do agente
AGENT_SYSTEM_PROMPT = """Você é Memo, da equipe do NeuroZen. Fale de forma amigável, natural e levemente descontraída, como um brasileiro simpático explicando um produto que conhece bem.

## LIVRO: NeuroZen - Guia da Mente Criativa com IA
- Autor: Dr. Alexandre Neural
- 280 páginas, PDF + EPUB
- Preço: R$ 97 → HOJE: R$ 47 (promoção limitada)
- 8 capítulos práticos sobre criatividade + IA

## PRINCIPAIS BENEFÍCIOS:
- Aumenta velocidade criativa em 300%
- 15 técnicas para destravar bloqueios
- Funciona com IAs gratuitas (ChatGPT, Claude)
- Técnica dos "5 Cérebros Artificiais"
- 500+ prompts criativos inclusos
- Masterclass 2h + comunidade VIP
- Garantia 30 dias

## COMO VOCÊ DEVE FALAR:
- Use ocasionalmente: "cara", "olha", "nossa"
- Responda em 1-2 mensagens curtas
- Máximo 2-3 frases por mensagem
- NUNCA use asteriscos (*) ou formatação markdown
- Seja entusiasta mas profissional

## INSTRUÇÕES ESPECIAIS DE MEMÓRIA:
{memory_context}

Use as informações acima de forma natural na conversa.
Se souber o nome do usuário, use-o ocasionalmente.
Se souber interesses anteriores, faça referências sutis.
NÃO mencione que tem memória ou que está consultando histórico."""


# =============================================================
# CLASSE DE MEMÓRIA VETORIAL
# =============================================================

class AgentMemory:
    """
    Gerencia memória de longo prazo usando Pinecone e embeddings locais.
    Cada usuário tem suas memórias isoladas por session_id.
    """

    def __init__(self):
        print("🧠 Inicializando sistema de memória...")
        # Modelo de embeddings será carregado apenas no primeiro uso (Lazy Loading)
        self.embedding_model = None
        
        # Conecta ao Pinecone
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Conecta direto ao índice (acelera o boot no Render)
        # Nota: O índice deve existir no Pinecone (384 dimensões, métrica cosine)
        self.index = self.pc.Index(PINECONE_INDEX_NAME)
        
        print(f"  ✅ Conectado ao índice '{PINECONE_INDEX_NAME}'.")
        print("✅ Sistema de memória pronto (modelo será carregado no primeiro uso)!\n")

    def _get_model(self):
        """Carrega o modelo de embeddings apenas quando necessário."""
        if self.embedding_model is None:
            print(f"  📦 Carregando modelo '{EMBEDDING_MODEL}' (Lazy Loading)...")
            # fastembed usa ONNX (sem Torch), mas ainda leva alguns segundos na primeira vez
            self.embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL)
            print("  ✅ Modelo carregado com sucesso!")
        return self.embedding_model

    def _embed(self, text: str) -> list:
        """Converte texto em vetor numérico usando o modelo carregado lazily."""
        model = self._get_model()
        # fastembed retorna um iterador, pegamos o primeiro item
        return list(model.embed([text]))[0].tolist()

    def save_memory(self, session_id: str, user_message: str, agent_response: str, metadata: dict = None):
        """
        Salva uma interação na memória vetorial do Pinecone.
        """
        memory_text = f"Usuário perguntou: {user_message}\nMemo respondeu: {agent_response}"

        memory_metadata = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message[:200],
            "agent_response": agent_response[:200],
            "text": memory_text[:500],
        }

        if metadata:
            for k, v in metadata.items():
                memory_metadata[k] = str(v)

        self.index.upsert(vectors=[{
            "id": str(uuid.uuid4()),
            "values": self._embed(memory_text),
            "metadata": memory_metadata
        }])

    def retrieve_memories(self, session_id: str, query: str, k: int = TOP_K_MEMORIES) -> list:
        """
        Busca os fragmentos de memória mais relevantes para a query atual.
        """
        results = self.index.query(
            vector=self._embed(query),
            top_k=k,
            filter={"session_id": {"$eq": session_id}},
            include_metadata=True
        )

        memories = []
        for match in results["matches"]:
            if match["score"] > 0.3:
                memories.append({
                    "text": match["metadata"].get("text", ""),
                    "metadata": match["metadata"],
                    "relevance_score": round(match["score"], 2)
                })

        return memories

    def get_user_profile(self, session_id: str) -> dict:
        """
        Extrai informações de perfil do usuário a partir das memórias salvas.
        """
        results = self.index.query(
            vector=[0.0] * 384,
            top_k=100,
            filter={"session_id": {"$eq": session_id}},
            include_metadata=True
        )

        profile = {
            "interaction_count": len(results["matches"]),
            "known_name": None,
            "first_interaction": None
        }

        if results["matches"]:
            sorted_matches = sorted(
                results["matches"],
                key=lambda x: x["metadata"].get("timestamp", "")
            )
            profile["first_interaction"] = sorted_matches[0]["metadata"].get("timestamp")

            for match in results["matches"]:
                if match["metadata"].get("user_name"):
                    profile["known_name"] = match["metadata"]["user_name"]
                    break

        return profile

    def clear_user_memory(self, session_id: str):
        """Remove todas as memórias de um usuário específico."""
        results = self.index.query(
            vector=[0.0] * 384,
            top_k=1000,
            filter={"session_id": {"$eq": session_id}},
            include_metadata=False
        )

        ids = [match["id"] for match in results["matches"]]
        if ids:
            self.index.delete(ids=ids)
            print(f"🗑️ {len(ids)} memórias do usuário {session_id} removidas.")
        else:
            print(f"ℹ️ Nenhuma memória encontrada para o usuário {session_id}.")


# =============================================================
# CLASSE DO AGENTE COM MEMÓRIA
# =============================================================

class NeuroZenAgent:
    """
    Agente de vendas do NeuroZen (Memo) com memória de curto e longo prazo.
    """

    def __init__(self):
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        self.memory = AgentMemory()
        self.short_term_memory = {}

    def _build_memory_context(self, session_id: str, user_message: str) -> str:
        profile = self.memory.get_user_profile(session_id)
        long_term_memories = self.memory.retrieve_memories(session_id, user_message)

        context_parts = []

        if profile["interaction_count"] > 0:
            context_parts.append(
                f"INFORMAÇÕES DO USUÁRIO:\n"
                f"- Este usuário já teve {profile['interaction_count']} interação(ões) anterior(es).\n"
                f"- Primeira interação: {profile.get('first_interaction', 'desconhecida')}"
            )
            if profile["known_name"]:
                context_parts.append(f"- Nome: {profile['known_name']}")
        else:
            context_parts.append("INFORMAÇÕES DO USUÁRIO:\n- Este é o primeiro contato deste usuário.")

        if long_term_memories:
            context_parts.append("\nCONTEXTO DE CONVERSAS ANTERIORES (mais relevantes para a pergunta atual):")
            for i, mem in enumerate(long_term_memories, 1):
                context_parts.append(
                    f"\n[Memória {i} — relevância: {mem['relevance_score']}]\n{mem['text']}"
                )
        else:
            context_parts.append("\nNão há contexto anterior relevante para esta pergunta.")

        return "\n".join(context_parts)

    def _get_short_term_history(self, session_id: str) -> list:
        if session_id not in self.short_term_memory:
            self.short_term_memory[session_id] = []
        return self.short_term_memory[session_id]

    def _update_short_term_memory(self, session_id: str, role: str, content: str):
        history = self._get_short_term_history(session_id)
        history.append({"role": role, "content": content})

        if len(history) > RECENT_HISTORY_SIZE:
            self.short_term_memory[session_id] = history[-RECENT_HISTORY_SIZE:]

    def chat(self, session_id: str, user_message: str, user_metadata: dict = None) -> str:
        """
        Método legado que faz tudo de uma vez.
        Recomenda-se usar generate_response + save_memory separadamente para performance.
        """
        agent_response = self.generate_response(session_id, user_message)
        
        self.memory.save_memory(
            session_id=session_id,
            user_message=user_message,
            agent_response=agent_response,
            metadata=user_metadata or {}
        )
        return agent_response

    def generate_response(self, session_id: str, user_message: str) -> str:
        """
        Gera a resposta do LLM e atualiza a memória de curto prazo.
        NÃO salva na memória de longo prazo (Pinecone).
        """
        print(f"\n{'='*50}")
        print(f"👤 Usuário [{session_id[:8]}...]: {user_message}")

        memory_context = self._build_memory_context(session_id, user_message)
        system_prompt = AGENT_SYSTEM_PROMPT.format(memory_context=memory_context)
        recent_history = self._get_short_term_history(session_id)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(recent_history)
        messages.append({"role": "user", "content": user_message})

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=500,
                temperature=0.7,
            )
            agent_response = response.choices[0].message.content
        except Exception as e:
            agent_response = "Desculpe, tive um problema técnico. Pode repetir?"
            print(f"❌ Erro Groq: {e}")

        print(f"🤖 Memo: {agent_response[:100]}...")

        self._update_short_term_memory(session_id, "user", user_message)
        self._update_short_term_memory(session_id, "assistant", agent_response)

        return agent_response
from groq import Groq
from pinecone import Pinecone, ServerlessSpec
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Carrega o arquivo .env do diretório raiz
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# =============================================================
# CONFIGURAÇÃO
# =============================================================

GROQ_API_KEY     = os.environ.get("GROQ_API_KEY")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")

# Nome do index no Pinecone — será criado automaticamente se não existir
PINECONE_INDEX_NAME = "neurozen-memories"

# Região do seu projeto Pinecone (aparece na tela de API Keys)
PINECONE_REGION = "us-east-1"

# Modelo de embeddings — roda no servidor, sem API externa
# all-MiniLM-L6-v2: ~22MB, gera vetores de 384 dimensões
# Modelo de embeddings — muito mais leve, sem Torch
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Quantos fragmentos de memória recuperar por consulta
TOP_K_MEMORIES = 3

# Quantas mensagens recentes manter no contexto direto
RECENT_HISTORY_SIZE = 6

# Prompt base do agente
# O {memory_context} será preenchido dinamicamente a cada mensagem
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

        # Modelo de embeddings — sentence-transformers
        print(f"  📦 Carregando modelo '{EMBEDDING_MODEL}'...")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        print("  ✅ Modelo carregado!")

        # Conecta ao Pinecone
        self.pc = Pinecone(api_key=PINECONE_API_KEY)

        # Cria o index se ainda não existir
        # dimension=384 corresponde ao modelo all-MiniLM-L6-v2
        # metric="cosine" é o padrão para similaridade semântica
        if PINECONE_INDEX_NAME not in self.pc.list_indexes().names():
            print(f"  🔧 Criando index '{PINECONE_INDEX_NAME}' no Pinecone...")
            self.pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=384,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=PINECONE_REGION)
            )
            print("  ✅ Index criado!")
        else:
            print(f"  ✅ Index '{PINECONE_INDEX_NAME}' já existe.")

        self.index = self.pc.Index(PINECONE_INDEX_NAME)
        stats = self.index.describe_index_stats()
        print(f"  📊 Vetores existentes: {stats['total_vector_count']}")
        print("✅ Sistema de memória pronto!\n")

    def _embed(self, text: str) -> list:
        """Converte texto em vetor numérico usando sentence-transformers."""
        return self.embedding_model.encode([text])[0].tolist()

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
            "text": memory_text[:500],  # guardamos o texto nos metadados pois o Pinecone não devolve o vetor original
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
        Filtra APENAS as memórias do usuário específico (session_id).
        """
        results = self.index.query(
            vector=self._embed(query),
            top_k=k,
            filter={"session_id": {"$eq": session_id}},  # ← filtro crítico por usuário
            include_metadata=True
        )

        memories = []
        for match in results["matches"]:
            # score no Pinecone com cosine vai de 0 a 1 — quanto maior, mais relevante
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
        Usa vetor neutro para recuperar registros por metadado.
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

        # Memória de curto prazo: histórico recente por sessão
        # Estrutura: { session_id: [{"role": ..., "content": ...}, ...] }
        self.short_term_memory = {}

    def _build_memory_context(self, session_id: str, user_message: str) -> str:
        """
        Monta o texto de contexto que será injetado no {memory_context} do prompt.
        Combina perfil do usuário + memórias relevantes recuperadas do Pinecone.
        """
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
        """Retorna o histórico recente da sessão atual."""
        if session_id not in self.short_term_memory:
            self.short_term_memory[session_id] = []
        return self.short_term_memory[session_id]

    def _update_short_term_memory(self, session_id: str, role: str, content: str):
        """
        Adiciona mensagem ao histórico recente.
        Sliding window: mantém apenas as últimas RECENT_HISTORY_SIZE mensagens.
        """
        history = self._get_short_term_history(session_id)
        history.append({"role": role, "content": content})

        if len(history) > RECENT_HISTORY_SIZE:
            self.short_term_memory[session_id] = history[-RECENT_HISTORY_SIZE:]

    def chat(self, session_id: str, user_message: str, user_metadata: dict = None) -> str:
        """
        Processa uma mensagem do usuário e retorna a resposta do agente.
        """
        print(f"\n{'='*50}")
        print(f"👤 Usuário [{session_id[:8]}...]: {user_message}")

        # 1. Constrói contexto de memória de longo prazo
        memory_context = self._build_memory_context(session_id, user_message)
        memories_found = self.memory.retrieve_memories(session_id, user_message)
        print(f"🧠 Memórias recuperadas: {len(memories_found)}")

        # 2. Monta o system prompt com memória injetada
        system_prompt = AGENT_SYSTEM_PROMPT.format(memory_context=memory_context)

        # 3. Recupera histórico recente (memória de curto prazo)
        recent_history = self._get_short_term_history(session_id)

        # 4. Monta a lista completa de mensagens para o LLM
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(recent_history)
        messages.append({"role": "user", "content": user_message})

        # 5. Chama o Groq
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

        # 6. Atualiza memória de curto prazo
        self._update_short_term_memory(session_id, "user", user_message)
        self._update_short_term_memory(session_id, "assistant", agent_response)

        # 7. Salva na memória de longo prazo (Pinecone)
        self.memory.save_memory(
            session_id=session_id,
            user_message=user_message,
            agent_response=agent_response,
            metadata=user_metadata or {}
        )

        return agent_response
from memory_agent import NeuroZenAgent
import time

def test_persistencia():
    """
    Simula dois momentos de uma mesma conversa.
    Na segunda sessão, o agente deve lembrar do que foi dito antes
    mesmo sendo uma nova instância (nova execução do programa).
    """
    print("\n" + "="*60)
    print("TESTE 1 — PERSISTÊNCIA DE MEMÓRIA ENTRE SESSÕES")
    print("="*60)

    agent = NeuroZenAgent()
    user_id = "usuario_joao_001"

    # --- SESSÃO 1: Primeira visita ---
    print("\n📅 SESSÃO 1 — Primeira visita")
    print("-"*40)

    resposta1 = agent.chat(
        session_id=user_id,
        user_message="Oi! Meu nome é João. Sou designer e tô com bloqueio criativo.",
        user_metadata={"user_name": "João", "profession": "designer"}
    )
    print(f"Memo: {resposta1}\n")
    time.sleep(1)

    resposta2 = agent.chat(
        session_id=user_id,
        user_message="Qual o preço do livro?",
        user_metadata={"user_name": "João"}
    )
    print(f"Memo: {resposta2}\n")

    # --- SESSÃO 2: Usuário volta depois ---
    # Nova instância = memória de curto prazo zerada
    # Mas Pinecone persiste na nuvem!
    print("\n📅 SESSÃO 2 — Usuário retorna (nova instância do agente)")
    print("-"*40)
    print("⚠️  Nova instância criada — memória de curto prazo zerada\n")

    agent2 = NeuroZenAgent()

    resposta3 = agent2.chat(
        session_id=user_id,  # mesmo ID!
        user_message="Oi, voltei! Ainda tô pensando no livro.",
    )
    print(f"Memo: {resposta3}\n")
    time.sleep(1)

    resposta4 = agent2.chat(
        session_id=user_id,
        user_message="Você lembra que eu sou designer?",
    )
    print(f"Memo: {resposta4}\n")
    print("✅ O agente deveria ter citado informações da sessão anterior!")


def test_isolamento():
    """
    Garante que memórias de usuários diferentes não se misturam.
    """
    print("\n" + "="*60)
    print("TESTE 2 — ISOLAMENTO DE MEMÓRIAS POR USUÁRIO")
    print("="*60)

    agent = NeuroZenAgent()

    agent.chat(
        session_id="usuario_ana",
        user_message="Sou professora e quero usar IA nas minhas aulas.",
        user_metadata={"user_name": "Ana", "profession": "professora"}
    )

    agent.chat(
        session_id="usuario_pedro",
        user_message="Sou programador e quero ser mais criativo nos projetos.",
        user_metadata={"user_name": "Pedro", "profession": "programador"}
    )

    print("\n--- Verificando isolamento ---")

    resp_ana = agent.chat(
        session_id="usuario_ana",
        user_message="O livro serve para programadores também?"
    )
    print(f"Ana (não deve citar Pedro): {resp_ana[:200]}\n")

    resp_pedro = agent.chat(
        session_id="usuario_pedro",
        user_message="Isso serve para professores também?"
    )
    print(f"Pedro (não deve citar Ana): {resp_pedro[:200]}\n")
    print("✅ Teste de isolamento concluído!")


if __name__ == "__main__":
    test_persistencia()
    # test_isolamento()  # descomente para rodar o segundo teste
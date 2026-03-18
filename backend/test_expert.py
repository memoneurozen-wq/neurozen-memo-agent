from memory_agent import NeuroZenAgent
import time
import os
from dotenv import load_dotenv

# Carrega o arquivo .env do diretório pai para testes locais
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def test_memo_expert():
    """
    Teste de 'Especialista com Memória':
    Verifica se o agente combina informações do catálogo (livro) 
    com preferências específicas salvas do usuário.
    """
    print("\n" + "="*60)
    print("TESTE — MEMO ESPECIALISTA E CONTEXTUAL")
    print("="*60)

    # Inicializa o agente
    # Nota: Em ambiente local, verifique se as chaves da API estão no .env
    try:
        agent = NeuroZenAgent()
    except Exception as e:
        print(f"❌ Erro ao inicializar o agente: {e}")
        return

    user_id = "test_expert_user_999"

    # 1. Estabelece um contexto de dor/necessidade
    print("\n👤 Passo 1: O usuário se apresenta com uma necessidade específica.")
    print("Mensagem: Oi Memo, sou ilustrador e perco muito tempo colorindo meus desenhos. Queria algo que me ajudasse nisso.")
    
    agent.chat(
        session_id=user_id,
        user_message="Oi Memo, sou ilustrador e perco muito tempo colorindo meus desenhos. Queria algo que me ajudasse nisso.",
        user_metadata={"profession": "ilustrador", "pain_point": "colorização"}
    )
    time.sleep(1)

    # 2. Pergunta técnica sobre o produto
    print("\n👤 Passo 2: O usuário faz uma pergunta técnica sobre o livro.")
    print("Mensagem: O livro ensina alguma técnica que me ajude a acelerar meu processo de trabalho?")
    print("--- O Memo deve responder sobre as técnicas E citar a colorização/ilustração ---")
    
    resposta = agent.chat(
        session_id=user_id,
        user_message="O livro ensina alguma técnica que me ajude a acelerar meu processo de trabalho?"
    )
    
    print(f"\n🤖 Resposta do Memo:\n{resposta}")
    
    print("\n" + "-"*60)
    print("✅ CRITÉRIOS DE SUCESSO:")
    print("1. O Memo mencionou a técnica dos '5 Cérebros Artificiais'?")
    print("2. Ele relacionou a resposta com o fato de você ser ILUSTRADOR?")
    print("3. Ele foi amigável e usou gírias naturais (cara, olha)?")
    print("="*60)

if __name__ == "__main__":
    test_memo_expert()

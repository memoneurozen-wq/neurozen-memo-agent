import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

# Carrega variáveis do arquivo .env
load_dotenv()

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "neurozen-memories"
PINECONE_REGION = "us-east-1" # Altere se necessário

def setup_index():
    if not PINECONE_API_KEY:
        print("❌ Erro: PINECONE_API_KEY não encontrada no .env")
        return

    pc = Pinecone(api_key=PINECONE_API_KEY)

    print("Verificando indices no Pinecone...")
    existing_indexes = [idx.name for idx in pc.list_indexes()]

    if PINECONE_INDEX_NAME not in existing_indexes:
        print(f"Criando index '{PINECONE_INDEX_NAME}'...")
        try:
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=384,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=PINECONE_REGION)
            )
            print(f"Index '{PINECONE_INDEX_NAME}' criado com sucesso!")
            print("Aguarde alguns segundos para o indice ficar pronto antes de rodar o inspect_db.py.")
        except Exception as e:
            print(f"Erro ao criar index: {e}")
    else:
        print(f"Index '{PINECONE_INDEX_NAME}' ja existe.")

if __name__ == "__main__":
    setup_index()

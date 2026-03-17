import os
from dotenv import load_dotenv
from pinecone import Pinecone

# Carrega as variáveis do .env automaticamente
load_dotenv()

PINECONE_API_KEY    = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "neurozen-memories"

pc    = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

# Estatísticas gerais do index
stats = index.describe_index_stats()
print(f"Total de vetores no index: {stats['total_vector_count']}")

# Listar memórias de um usuário específico
results = index.query(
    vector=[0.0] * 384,
    top_k=50,
    filter={"session_id": {"$eq": "usuario_joao_001"}},
    include_metadata=True
)

print(f"\nMemórias do usuário 'usuario_joao_001': {len(results['matches'])}")

for match in results["matches"]:
    meta = match["metadata"]
    print(f"\n📅 {meta.get('timestamp', 'sem data')}")
    print(f"📝 {meta.get('text', '')[:150]}...")
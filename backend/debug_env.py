from dotenv import load_dotenv
import os
import sys

print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.path}")
loaded = load_dotenv()
print(f"Dotenv loaded: {loaded}")
print(f"PINECONE_API_KEY present: {'PINECONE_API_KEY' in os.environ}")

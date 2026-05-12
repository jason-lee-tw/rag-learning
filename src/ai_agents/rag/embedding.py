import os

from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVectorStore


def embedding():
  OLLAMA_BASE_URL=os.getenv('OLLAMA_BASE_URL')

  if OLLAMA_BASE_URL is None:
    raise RuntimeError('`OLLAMA_BASE_URL` is not defined.')
  
  # EmbeddingGemma dimension is from 128 to 768
  embedding_model = OllamaEmbeddings(
    model='embeddinggemma:latest',
    dimensions=768,
    base_url=OLLAMA_BASE_URL
  )
  
  pass
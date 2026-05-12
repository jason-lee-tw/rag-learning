from uuid import uuid7

from fastapi import APIRouter
from langchain_core.documents import Document

from ai_agents.rag.embedding import embedding
from modules.rag.dtos.create_document import CreateDocumentReqBody

router = APIRouter(prefix='/rag')

@router.post('/')
def create_documents(body: CreateDocumentReqBody):
  documents = body.documents

  parsed_documents = [
    Document(
      page_content=doc.content,
      metadata={
        "id": str(uuid7()),
        "source": doc.source,
        "document_name": doc.full_name
      }
    ) for doc in documents
  ]

  embedding(documents=parsed_documents)

  return {
    "message": "ok"
  }
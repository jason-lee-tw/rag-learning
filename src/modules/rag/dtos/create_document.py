from pydantic import BaseModel


class OriginalDocuments(BaseModel):
  full_name: str
  content: str
  source: str


class CreateDocumentReqBody(BaseModel):
  documents: list[OriginalDocuments]
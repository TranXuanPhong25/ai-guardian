from pydantic import BaseModel

class GeminiRequest(BaseModel):
    prompt: str

class GeminiResponse(BaseModel):
    response: str

class RagQueryRequest(BaseModel):
    query: str

class RagQueryResponse(BaseModel):
    context: str

class RagUpdateRequest(BaseModel):
    document_id: int
    content: str

class RagUpdateResponse(BaseModel):
    status: str
    message: str

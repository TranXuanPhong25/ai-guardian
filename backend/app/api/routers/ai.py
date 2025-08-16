from fastapi import APIRouter, Depends
from app.schemas import ai as ai_schema
from app.services import chat_service


router = APIRouter(prefix="/ai", tags=["AI"])

# Chỉ gửi prompt cho gemini

@router.post("/rag/query", response_model=ai_schema.RagQueryResponse)
def rag_query_api(request: ai_schema.RagQueryRequest):
    # TODO: Gọi vectorDB thực tế
    context = chat_service.rag_query(request.query)
    return ai_schema.RagQueryResponse(context=context)

@router.post("/rag/update", response_model=ai_schema.RagUpdateResponse)
def rag_update_api(request: ai_schema.RagUpdateRequest):
    # TODO: Gọi vectorDB thực tế
    status, message = chat_service.rag_update(request.content)
    return ai_schema.RagUpdateResponse(status=status, message=message)

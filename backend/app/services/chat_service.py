# Hàm phát hiện thông tin nhạy cảm (mock, có thể thay thế bằng AI thực tế)
def detect_sensitive(content: str) -> dict:
    sensitive = "John" in content
    entities = []
    if sensitive:
        entities.append({"type": "PERSON", "value": "John Doe"})
    return {"sensitive": sensitive, "entities": entities}
def rag_update(content: str):
    # MOCK: Trả về status và message mẫu
    return "success", f"Document updated with content: {content}"

from sqlalchemy.orm import Session
from app.schemas.mask import MaskMappingResponse


# Hàm masking nội dung: trả về masked_text (đảo ngược chuỗi) và mapping (mock)
def mask_text(conversation_id: str, content: str, db: Session) -> dict:
    import datetime
    # Giả lập masking: đảo ngược chuỗi
    masked_text = content[::-1]
    mapping = {"mock": True, "masked": True}
    now = datetime.datetime.now(datetime.timezone.utc)
    # Có thể lưu mapping vào DB ở đây nếu muốn
    return {
        "masked_text": masked_text,
        "mapping": mapping,
        "conversation_id": conversation_id,
        "created_at": now
    }

# Hàm unmask nội dung: nhận masked_text và mapping, trả về text gốc (giả lập: đảo ngược lại chuỗi)
def unmask_text(masked_text: str, mapping: dict) -> dict:
    # Giả lập: đảo ngược lại chuỗi
    text = masked_text[::-1] if masked_text else ""
    return {"text": text}
def rag_query(query: str) -> str:
    # MOCK: Trả về context mẫu
    return "mock context for query"

async def send_to_gemini(prompt: str) -> str:
    # MOCK: Trả về response mẫu
    return "mock gemini response"
import asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
import os

TEMPLATE = """You are a helpful assistant. Respond to all user input with clear, concise, and informative responses.

User: {input}
AI:
"""


async def process_chat(model_id: str, messages, db: Session, chat_session_id: UUID):
    current_message_content = messages[-1].content
    prompt = ChatPromptTemplate.from_template(TEMPLATE)

    # Map model IDs to Gemini models (updated model names)
    gemini_model_map = {
        "gpt-3.5-turbo": "gemini-2.0-flash",
        "gpt-4": "gemini-2.0-pro",
        "gemini-pro": "gemini-2.0-flash",
        "gemini-2.0-pro": "gemini-2.0-pro",
        "gemini-2.0-flash": "gemini-2.0-flash"
    }

    gemini_model = gemini_model_map.get(model_id, "gemini-2.0-flash")

    model = ChatGoogleGenerativeAI(
        model=gemini_model,
        temperature=0.8,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    chain = prompt | model | StrOutputParser()

    async def generate_chat_responses():
        from app.models import Message

        full_response = ""
        try:
            async for chunk in chain.astream({"input": current_message_content}):
                if chunk:  # Make sure chunk is not empty
                    # Accumulate the chunks
                    full_response += chunk

                    # Format the chunk properly for streaming
                    # Escape quotes and newlines for JSON format
                    escaped_chunk = chunk.replace('"', '\\"').replace('\n', '\\n')
                    yield f'0:"{escaped_chunk}"\n'
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            # Save the accumulated response to the database even if streaming was interrupted
            if full_response:
                db.add(Message(
                    chat_session_id=chat_session_id,
                    role="assistant",
                    content=full_response
                ))
                db.commit()

    response = StreamingResponse(generate_chat_responses())
    response.headers["x-vercel-ai-data-stream"] = "v1"
    return response
# Import các thư viện cần thiết từ FastAPI và các module nội bộ

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.models import ChatSession, Message
from app.services.RAG_service import GeminiChat
from app.api.routers.mask import mask_content, unmask_content, validate_sensitive
from app.schemas.mask import MaskRequest
from uuid import uuid4, UUID
from datetime import datetime
from app.database.database import get_db

# API unmask response của AI dựa trên mapping
# Nhận vào masked_text (response của AI) và mapping, trả về text đã unmask
@router.post("/unmask-response")
def unmask_ai_response(body: dict, db: Session = Depends(get_db)):
    masked_text = body.get("masked_text")
    mapping = body.get("mapping")
    if not masked_text or not mapping:
        return {"error": "masked_text và mapping là bắt buộc"}
    result = unmask_content({"masked_text": masked_text, "mapping": mapping}, db)
    return result


# Khởi tạo router cho nhóm API chat, prefix là /chat, gắn tag "Chat" để phân loại trên docs
router = APIRouter(prefix="/chat", tags=["Chat"])

# POST /chat/send
from uuid import UUID
from fastapi import Request

# API gửi tin nhắn chat
# Nhận vào body gồm conversation_id, message, user_id; thực hiện masking, lưu session, lưu message, gọi AI, lưu AI response
@router.post("/send")
async def send_chat(body: dict, request: Request, db: Session = Depends(get_db)):
    conversation_id = body.get("conversation_id") or str(uuid4())
    message = body.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    user_id = body.get("user_id") or "00000000-0000-0000-0000-000000000001"

    # 1. Detect sensitive bằng API validate_sensitive
    from app.api.routers.mask import validate_sensitive
    sensitive_result = await validate_sensitive({"content": message})
    # Chuẩn hóa output cho giống cũ
    alert = sensitive_result.get("alert")
    sensitive = bool(alert)
    entities = [alert] if alert else []

    # 2. Masking nội dung user gửi qua API mask_content
    mask_request = MaskRequest(conversation_id=conversation_id, content=message)
    mask_result = mask_content(mask_request, db)
    masked_text = mask_result["masked_text"]
    mapping = mask_result["mapping"]

    # Tìm hoặc tạo mới chat session
    chat_session = db.query(ChatSession).filter(ChatSession.id == conversation_id).first()
    if not chat_session:
        chat_session = ChatSession(id=conversation_id, user_id=user_id, title="New Chat")
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)
    chat_session.updated_at = datetime.utcnow()
    db.commit()

    # Lưu message của user
    user_msg = Message(chat_session_id=conversation_id, role="user", content=message)
    db.add(user_msg)
    db.commit()

    # 3. Gửi masked_text cho Gemini LLM
    gemini = GeminiChat()
    ai_response = gemini(masked_text)

    # 4. Unmask response của AI dựa vào mapping
    unmasked_result = unmask_content({"masked_text": ai_response, "mapping": mapping}, db)
    unmasked_text = unmasked_result.get("text", "")

    # 5. Lưu message AI trả lời (có thể lưu cả masked và unmasked nếu muốn)
    ai_msg = Message(chat_session_id=conversation_id, role="ai", content=unmasked_text)
    db.add(ai_msg)
    db.commit()

    return {
        "conversation_id": str(conversation_id),
        "user_message": message,
        "ai_response": unmasked_text,
        "masked": mapping,
        "sensitive": sensitive_result.get("sensitive", False),
        "entities": sensitive_result.get("entities", [])
    }

# GET /chat/history
# API lấy danh sách lịch sử chat (GET /chat/history)
# Trả về danh sách các session chat, sắp xếp theo thời gian cập nhật mới nhất
@router.get("/history")
def chat_history(db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()
    result = []
    for s in sessions:
        last_msg = db.query(Message).filter(Message.chat_session_id == s.id).order_by(Message.created_at.desc()).first()
        result.append({
            "conversation_id": str(s.id),
            "last_message": last_msg.content if last_msg else None,
            "updated_at": s.updated_at.isoformat()
        })
    return result

# GET /chat/{conversation_id}
# API lấy chi tiết lịch sử chat theo conversation_id (GET /chat/{conversation_id})
# Trả về danh sách message của session, kiểm tra hợp lệ UUID và tồn tại session
@router.get("/{conversation_id}")
def chat_detail(conversation_id: str, db: Session = Depends(get_db)):
    # Kiểm tra hợp lệ UUID
    try:
        uuid_obj = UUID(conversation_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Chat session not found")
    session = db.query(ChatSession).filter(ChatSession.id == conversation_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    messages = db.query(Message).filter(Message.chat_session_id == conversation_id).order_by(Message.created_at.asc()).all()
    return {
        "conversation_id": str(conversation_id),
        "messages": [
            {"role": m.role, "content": m.content} for m in messages
        ]
    }

# DELETE /chat/{conversation_id}
# API xóa một session chat theo conversation_id (DELETE /chat/{conversation_id})
# Kiểm tra hợp lệ UUID, xóa toàn bộ message và session khỏi DB
@router.delete("/{conversation_id}")
def delete_chat(conversation_id: str, db: Session = Depends(get_db)):
    # Kiểm tra hợp lệ UUID
    try:
        uuid_obj = UUID(conversation_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Chat session not found")
    session = db.query(ChatSession).filter(ChatSession.id == conversation_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    db.query(Message).filter(Message.chat_session_id == conversation_id).delete()
    db.delete(session)
    db.commit()
    return {"message": "Deleted"}
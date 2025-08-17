


from fastapi import APIRouter, Depends
from app.schemas import mask as mask_schema
from app.database.database import get_db
from sqlalchemy.orm import Session
from app.models.mask_mapping import MaskMapping
from app.services.masking_service import PIIMaskerService
from app.services.unmasking_service import PIIUnmaskerService
from app.services.notification_service import notification_service
# Khởi tạo router cho nhóm API mask, prefix là /mask, gắn tag "Mask" để phân loại trên docs
router = APIRouter(prefix="/mask", tags=["Mask"])
pii_masker_service = PIIMaskerService()
pii_unmasker_service = PIIUnmaskerService()
# Phần này của AI
# API masking nội dung hội thoại
# Nhận conversation_id và content, gọi service masking, lưu mapping vào DB, trả về masked_text và mapping
@router.post("/", response_model=dict)
async def mask_content(request: mask_schema.MaskRequest, db: Session = Depends(get_db)):
    masked_text, mapping = await pii_masker_service.mask_text(request.content)
    # Lưu mapping vào DB
    mask_db = db.get(MaskMapping, request.session_id)
    if mask_db:
        mask_db.mapping = mask_db.mapping | mapping
    else:
        mask_db = MaskMapping(session_id=request.session_id, mapping=mapping)
        db.add(mask_db)
    db.commit()
    db.refresh(mask_db)
    return {"masked_text": masked_text, "mapping": mapping, "mapping_id": mask_db.session_id}
# Phần này của AI
# API unmask nội dung đã được masking
# Nhận masked_text và mapping, gọi service unmask, trả về text gốc
@router.post("/unmask", response_model=dict)
def unmask_content(request: dict):
    try:
        masked_text = request.get("masked_text", "")
        mapping = request.get("mapping", {})
        
        if not masked_text:
            return {"text": ""}
        
        # Gọi service unmask (không async nữa)
        text = pii_unmasker_service.unmask_text(masked_text, mapping)
        return {"text": text}
    except Exception as e:
        return {"error": str(e), "text": masked_text or ""}

# API lấy mapping masking của một hội thoại theo conversation_id
# Nhận chat_id, truy vấn DB để lấy mapping, trả về mapping nếu có
@router.get("/mask-mapping/{chat_id}", response_model=dict)
def get_mask_mapping(chat_id: int, db: Session = Depends(get_db)):
    mapping_obj = db.query(MaskMapping).filter(MaskMapping.session_id == chat_id).first()
    mapping = mapping_obj.mapping if mapping_obj else {}
    return {"mapping": mapping}

# API kiểm tra nội dung có chứa thông tin nhạy cảm không
# Nhận text/content từ request, gọi service AI để phát hiện nhạy cảm, trả về kết quả từ service
@router.post("/validate-sensitive", response_model=dict)
async def validate_sensitive(request: dict):
    content = request.get("text") or request.get("content") or ""
    # Gọi notification_service để phát hiện PII và sinh cảnh báo
    alert_message = await notification_service.generate_pii_alert(content)
    return {"alert": alert_message} if alert_message else {"alert": None}

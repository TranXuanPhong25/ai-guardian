
# notification_sservice.py
# Service để phát hiện PII trong prompt của người dùng và sinh cảnh báo nếu có.
# Sử dụng Presidio Analyzer để nhận diện các entity nhạy cảm.

from typing import List, Optional
import logging
from presidio_analyzer import AnalyzerEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationService:
    """
    Service để phát hiện PII trong prompt của người dùng và sinh cảnh báo nếu có.
    - Sử dụng Presidio Analyzer để nhận diện các entity nhạy cảm.
    """
    def __init__(self):
        # Khởi tạo Presidio Analyzer
        self.analyzer: AnalyzerEngine = AnalyzerEngine()

    async def detect_pii(self, text: str) -> List[dict]:
        """
        Phát hiện các entity PII trong văn bản.
        - Trả về danh sách dict chứa thông tin entity.
        """
        try:
            analyzer_results = self.analyzer.analyze(text=text, language='en')
            return [
                {
                    "entity_type": res.entity_type,
                    "start": res.start,
                    "end": res.end,
                    "score": res.score,
                    "text": text[res.start:res.end]
                } for res in analyzer_results
            ]
        except Exception as e:
            logger.error(f"Error detecting PII: {str(e)}")
            return []

    async def generate_pii_alert(self, text: str) -> Optional[str]:
        """
        Sinh thông báo cảnh báo nếu phát hiện PII trong prompt.
        - Trả về chuỗi cảnh báo hoặc None nếu không phát hiện PII.
        """
        pii_entities = await self.detect_pii(text)
        if pii_entities:
            entity_types = set(entity["entity_type"] for entity in pii_entities)
            alert_message = f"Cảnh báo: Phát hiện thông tin cá nhân (PII) trong prompt của bạn. Các loại PII: {', '.join(entity_types)}. Hãy cân nhắc chỉnh sửa để bảo vệ dữ liệu cá nhân."
            logger.info(alert_message)
            return alert_message
        return None

# Khởi tạo instance dùng chung cho service cảnh báo PII
notification_service = NotificationService()
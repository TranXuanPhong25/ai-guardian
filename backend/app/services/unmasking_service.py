
# unmasking_service.py
# Service để khôi phục lại văn bản gốc từ văn bản đã được masking (unmasking).
# Sử dụng mapping được truyền vào để thay thế pseudonym về giá trị gốc.

import logging
from typing import Optional, Dict

class PIIUnmaskerService:
    """
    Service để khôi phục lại văn bản gốc từ văn bản đã được masking (unmasking).
    - Sử dụng mapping dictionary để thay thế pseudonym về giá trị gốc.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def unmask_text(self, text: str, mapping: Dict[str, str]) -> str:
        """
        Thay thế tất cả pseudonym trong text bằng giá trị gốc dựa trên mapping.
        - text: Văn bản đã được masking.
        - mapping: Dict với key là pseudonym và value là original value
        - Trả về văn bản đã được unmask (khôi phục).
        """
        try:
            if not text or not mapping:
                return text

            unmasked_text = text
            
            # Sắp xếp theo độ dài pseudonym giảm dần để tránh thay thế nhầm lẫn chuỗi con
            sorted_mappings = sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True)
            
            for pseudonym, original_value in sorted_mappings:
                unmasked_text = unmasked_text.replace(pseudonym, original_value)

            self.logger.info("Unmasking completed successfully.")
            return unmasked_text

        except Exception as e:
            self.logger.error(f"Error unmasking text: {str(e)}")
            return text

# Khởi tạo instance dùng chung cho service unmasking PII
pii_unmasker_service = PIIUnmaskerService()
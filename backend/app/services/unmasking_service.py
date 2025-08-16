
# unmasking_service.py
# Service để khôi phục lại văn bản gốc từ văn bản đã được masking (unmasking).
# Truy vấn bảng mapping trong database để thay thế pseudonym về giá trị gốc.

import asyncpg
import logging
import os

from typing import Optional

class PIIUnmaskerService:
    """
    Service để khôi phục lại văn bản gốc từ văn bản đã được masking (unmasking).
    - Truy vấn bảng mapping trong database để thay thế pseudonym về giá trị gốc.
    """
    def __init__(self):
        # Lấy cấu hình database từ .env
        self.db_url = os.getenv('DATABASE_URL')
        self.logger = logging.getLogger(__name__)

    async def unmask_text(self, text: str) -> Optional[str]:
        """
        Thay thế tất cả pseudonym trong text bằng giá trị gốc dựa trên bảng mapping.
        - text: Văn bản đã được masking.
        - Trả về văn bản đã được unmask (khôi phục).
        """
        try:
            async with asyncpg.create_pool(dsn=self.db_url) as pool:
                async with pool.acquire() as conn:
                    result = await conn.fetch("""
                        SELECT pseudonymized_value, original_value 
                        FROM pii_mappings
                    """)

                    # Sắp xếp theo độ dài pseudonym giảm dần để tránh thay thế nhầm lẫn chuỗi con
                    mappings = sorted(result, key=lambda x: len(x["pseudonymized_value"]), reverse=True)

                    unmasked_text = text
                    for row in mappings:
                        unmasked_text = unmasked_text.replace(row["pseudonymized_value"], row["original_value"])

                    self.logger.info("Unmasking completed successfully.")
                    return unmasked_text

        except Exception as e:
            self.logger.error(f"Error unmasking text: {str(e)}")
            return text

# Khởi tạo instance dùng chung cho service unmasking PII
pii_unmasker_service = PIIUnmaskerService()
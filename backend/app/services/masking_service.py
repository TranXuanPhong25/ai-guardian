
# masking_service.py
# Service để phát hiện và ẩn danh hóa (masking) thông tin nhạy cảm (PII) trong văn bản.
# Sử dụng Presidio để nhận diện PII và sinh pseudonym, lưu mapping vào database.

import hashlib
import asyncpg
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
import os
from dotenv import load_dotenv, find_dotenv
from typing import Optional


load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

class PIIMaskerService:
    """
    Service để phát hiện và masking (ẩn danh hóa) thông tin nhạy cảm (PII) trong văn bản.
    - Sử dụng Presidio để nhận diện PII.
    - Sinh pseudonym cho từng loại PII và lưu mapping vào database.
    """
    def __init__(self):
        # Lấy secret key và cấu hình database từ .env
        self.secret_key = os.getenv('SECRET_KEY', 'my_secret_key_123')
        self.db_url = os.getenv('DATABASE_URL')
        # Khởi tạo Presidio Analyzer và Anonymizer
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        import logging
        self.logger = logging.getLogger(__name__)

    async def initialize_database(self) -> None:
        """
        Khởi tạo bảng và index cần thiết cho lưu mapping PII trong database.
        """
        async with asyncpg.create_pool(dsn=self.db_url) as pool:
            async with pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS pii_mappings (
                        id SERIAL PRIMARY KEY,
                        entity_type VARCHAR(50) NOT NULL,
                        original_value TEXT NOT NULL,
                        pseudonymized_value TEXT NOT NULL,
                        hash_key TEXT NOT NULL,
                        CONSTRAINT unique_entity_value UNIQUE (entity_type, original_value)
                    );
                    CREATE INDEX IF NOT EXISTS idx_entity_hash ON pii_mappings (entity_type, hash_key);
                """)

    async def save_pii_mapping(self, entity_type: str, original_value: str, pseudonymized_value: str) -> str:
        """
        Lưu mapping giữa giá trị gốc và pseudonym vào database.
        Nếu đã tồn tại, cập nhật lại pseudonym và hash_key.
        """
        hash_val = hashlib.sha256((original_value + self.secret_key).encode()).hexdigest()
        async with asyncpg.create_pool(dsn=self.db_url) as pool:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO pii_mappings (entity_type, original_value, pseudonymized_value, hash_key)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (entity_type, original_value)
                    DO UPDATE SET pseudonymized_value = EXCLUDED.pseudonymized_value,
                                  hash_key = EXCLUDED.hash_key
                """, entity_type, original_value, pseudonymized_value, hash_val)
        return pseudonymized_value

    async def generate_pseudonym(self, entity_type: str, value: str) -> str:
        """
        Sinh pseudonym cho một giá trị PII dựa trên loại entity.
        - entity_type: Loại thông tin nhạy cảm (NAME, EMAIL_ADDRESS, ...)
        - value: Giá trị gốc cần ẩn danh hóa
        """
        hash_val = hashlib.sha256((value + self.secret_key).encode()).hexdigest()[:6].upper()
        pseudonym_map = {
            "NAME": f"Name_{hash_val}",
            "EMAIL_ADDRESS": f"Email_{hash_val}@example.com",
            "PHONE_NUMBER": f"Phone_{hash_val}",
            "DATE_TIME": f"Date_{hash_val}",
            "CREDIT_CARD": f"CC_{hash_val}",
            "ADDRESS": f"Address_{hash_val}",
            "DEFAULT": f"PII_{hash_val}"
        }
        pseudonym = pseudonym_map.get(entity_type, pseudonym_map["DEFAULT"])
        return await self.save_pii_mapping(entity_type, value, pseudonym)

    async def mask_text(self, text: str) -> Optional[str]:
        """
        Phát hiện và masking tất cả PII trong văn bản đầu vào.
        - Trả về văn bản đã được thay thế các giá trị PII bằng pseudonym.
        """
        try:
            # Phân tích văn bản để tìm các entity PII
            analyzer_results = self.analyzer.analyze(text=text, language='en')
            # Sắp xếp ngược để thay thế từ cuối lên đầu, tránh sai vị trí
            analyzer_results = sorted(analyzer_results, key=lambda x: x.start, reverse=True)
            masked_text = text

            for res in analyzer_results:
                original_value = text[res.start:res.end]
                pseudonym = await self.generate_pseudonym(res.entity_type, original_value)
                masked_text = masked_text[:res.start] + pseudonym + masked_text[res.end:]

            return masked_text
        except Exception as e:
            # Nếu có lỗi, log và trả về None
            self.logger.error(f"Error masking text: {str(e)}")
            return None


# Khởi tạo instance dùng chung cho service masking PII
pii_masker_service = PIIMaskerService()
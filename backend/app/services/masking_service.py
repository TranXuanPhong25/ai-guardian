import hashlib
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
import os
from dotenv import load_dotenv, find_dotenv
from typing import Optional, Tuple, Dict
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.models.pii_mapping import PiiMapping
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))


class PIIMaskerService:
    """
    Service để phát hiện và ẩn danh hóa (masking) thông tin nhạy cảm (PII) trong văn bản.
    - Sử dụng Presidio để nhận diện PII.
    - Sinh pseudonym cho từng loại PII và lưu mapping vào database.
    """

    def __init__(self):
        # Lấy secret key từ .env
        self.secret_key = os.getenv('SECRET_KEY', 'my_secret_key_123')
        # Khởi tạo Presidio Analyzer và Anonymizer
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.logger = logging.getLogger(__name__)
        # Thread pool cho database operations
        self.executor = ThreadPoolExecutor(max_workers=4)

    def _save_pii_mapping_sync(self, entity_type: str, original_value: str, pseudonymized_value: str) -> str:
        """
        Sync version của save_pii_mapping để chạy trong thread pool
        """
        hash_val = hashlib.sha256((original_value + self.secret_key).encode()).hexdigest()
        
        db = SessionLocal()
        try:
            # Tìm xem đã có mapping này chưa
            existing = db.query(PiiMapping).filter(
                PiiMapping.entity_type == entity_type,
                PiiMapping.original_value == original_value
            ).first()
            
            if existing:
                # Cập nhật mapping hiện có
                existing.pseudonymized_value = pseudonymized_value
                existing.hash_key = hash_val
            else:
                # Tạo mapping mới
                new_mapping = PiiMapping(
                    entity_type=entity_type,
                    original_value=original_value,
                    pseudonymized_value=pseudonymized_value,
                    hash_key=hash_val
                )
                db.add(new_mapping)
            
            db.commit()
            return pseudonymized_value
            
        except Exception as e:
            self.logger.error(f"Error saving PII mapping: {e}")
            db.rollback()
            return pseudonymized_value
        finally:
            db.close()

    async def save_pii_mapping(self, entity_type: str, original_value: str, pseudonymized_value: str) -> str:
        """
        Async version - lưu mapping giữa giá trị gốc và pseudonym vào database.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self._save_pii_mapping_sync, 
            entity_type, 
            original_value, 
            pseudonymized_value
        )

    async def generate_pseudonym(self, entity_type: str, value: str) -> str:
        """
        Sinh pseudonym cho một giá trị PII dựa trên loại entity.
        - entity_type: Loại thông tin nhạy cảm (NAME, EMAIL_ADDRESS, ...)
        - value: Giá trị gốc cần ẩn danh hóa
        """
        hash_val = hashlib.sha256((value + self.secret_key).encode()).hexdigest()[:6].upper()
        pseudonym_map = {
            "PERSON": f"Name_{hash_val}",
            "EMAIL_ADDRESS": f"Email_{hash_val}@example.com",
            "PHONE_NUMBER": f"Phone_{hash_val}",
            "US_SSN": f"US_SSN_{hash_val}",
            "DATE_TIME": f"Date_{hash_val}",
            "CREDIT_CARD": f"CC_{hash_val}",
            "ADDRESS": f"Address_{hash_val}",
            "DEFAULT": f"PII_{hash_val}",
            "LOC": f"LOCATION_{hash_val}",
            "LOCATION": f"LOCATION_{hash_val}",
            "GPE": f"LOCATION_{hash_val}",
            "ORG": f"ORGANIZATION_{hash_val}",
            "ORGANIZATION": f"ORGANIZATION_{hash_val}",
            "NORP": f"NRP_{hash_val}",
            "AGE": f"AGE_{hash_val}",
            "ID": f"ID_{hash_val}",
            "PATIENT": f"PERSON_{hash_val}",
            "STAFF": f"PERSON_{hash_val}",
            "HOSP": f"ORGANIZATION_{hash_val}",
            "PATORG": f"ORGANIZATION_{hash_val}",
            "DATE": f"DATE_TIME_{hash_val}",
            "TIME": f"DATE_TIME_{hash_val}",
            "HCW": f"PERSON_{hash_val}",
            "HOSPITAL": f"ORGANIZATION_{hash_val}",
            "FACILITY": f"LOCATION_{hash_val}",
            "VENDOR": f"ORGANIZATION_{hash_val}"
        }
        pseudonym = pseudonym_map.get(entity_type, pseudonym_map["DEFAULT"])
        return await self.save_pii_mapping(entity_type, value, pseudonym)

    async def mask_text(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Phát hiện và masking tất cả PII trong văn bản đầu vào sử dụng AnonymizerEngine.
        - Trả về tuple (masked_text, mapping) với mapping từ pseudonym -> original_value
        """
        try:
            if not text or not text.strip():
                return "", {}

            # Phân tích văn bản để tìm các entity PII
            analyzer_results = self.analyzer.analyze(text=text, language='en')
            
            if not analyzer_results:
                return text, {}

            # Tạo danh sách các operator tùy chỉnh cho từng entity và mapping
            operators = {}
            mapping = {}
            
            # Tạo tất cả pseudonyms async để speed up
            pseudonym_tasks = []
            for res in analyzer_results:
                original_value = text[res.start:res.end]
                task = self.generate_pseudonym(res.entity_type, original_value)
                pseudonym_tasks.append((res, original_value, task))
            
            # Chờ tất cả pseudonyms được tạo
            for res, original_value, task in pseudonym_tasks:
                pseudonym = await task
                
                # Presidio AnonymizerEngine cần OperatorConfig object
                operators[res.entity_type] = OperatorConfig("replace", {"new_value": pseudonym})
                
                # Lưu mapping từ pseudonym về original value
                mapping[pseudonym] = original_value

            # Sử dụng AnonymizerEngine để xử lý thay thế
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=analyzer_results,
                operators=operators
            )

            return anonymized_result.text, mapping
            
        except Exception as e:
            # Nếu có lỗi, log và trả về text gốc với mapping rỗng
            self.logger.error(f"Error masking text: {str(e)}")
            return text, {}


# Khởi tạo instance dùng chung cho service masking PII
pii_masker_service = PIIMaskerService()
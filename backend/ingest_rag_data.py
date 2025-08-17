import sys
import logging
from pathlib import Path

import warnings

from app.config import Config
from app.services.agents.rag_agent import DocumentRAG

warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add project root to path if needed
sys.path.append(str(Path(__file__).parent.parent))

# Import components

# Load configuration
config = Config()

rag = DocumentRAG(config)

# Document ingestion
def data_ingestion():
    """
    Ingest các file văn bản đã xử lý sẵn từ thư mục data/raw/ vào hệ thống RAG.
    
    Returns:
        bool: True nếu ingestion thành công, False nếu thất bại
    """
    try:
        # Luôn sử dụng thư mục data/raw/
        dir_path = Path("data/raw/")
        if not dir_path.exists():
            print("Lỗi: Thư mục 'data/raw/' không tồn tại.")
            logging.error("Thư mục 'data/raw/' không tồn tại.")
            return False
        if not dir_path.is_dir():
            print("Lỗi: 'data/raw/' không phải là thư mục.")
            logging.error("'data/raw/' không phải là thư mục.")
            return False
        
        # Kiểm tra xem có file .txt nào không
        txt_files = [f for f in dir_path.glob("*.txt")]
        if not txt_files:
            print("Lỗi: Không tìm thấy file văn bản (.txt) nào trong 'data/raw/'.")
            logging.warning("Không tìm thấy file văn bản (.txt) trong 'data/raw/'.")
            return False
        
        # Process và ingest các file
        result = rag.ingest_directory(str(dir_path))
        return result.get("success", False)
        
    except Exception as e:
        print(f"Lỗi trong quá trình ingestion: {str(e)}")
        logging.error(f"Ingestion thất bại: {str(e)}")
        return False

# Run ingestion
if __name__ == "__main__":
    # Kiểm tra xem thư mục mặc định có tồn tại không
    if not Path("data/raw/").exists():
        print("Lỗi: Thư mục mặc định 'data/raw/' không tồn tại.")
        logging.error("Thư mục mặc định 'data/raw/' không tồn tại.")
        sys.exit(1)
    
    try:
        ingestion_success = data_ingestion()
        
        if ingestion_success:
            print("Ingest tài liệu thành công.")
            logging.info("Ingest tài liệu thành công.")
        else:
            print("Ingest thất bại.")
            logging.error("Ingest thất bại.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("Bị gián đoạn bởi người dùng.")
        logging.info("Bị gián đoạn bởi người dùng.")
        sys.exit(1)
    except Exception as e:
        print(f"Lỗi: {str(e)}")
        logging.error(f"Lỗi: {str(e)}")
        sys.exit(1)
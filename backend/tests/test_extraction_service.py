import os
import unittest
from unittest.mock import patch, mock_open, MagicMock
import pytest
import pandas as pd
from app.services.extraction_service import FileExtractorService

class TestFileExtractorService(unittest.TestCase):
   def setUp(self):
      # Mock the model loading since we don't want to actually load models in tests
      with patch('app.services.extraction_service.AutoProcessor.from_pretrained'), \
          patch('app.services.extraction_service.AutoModelForVision2Seq.from_pretrained'), \
          patch('app.services.extraction_service.torch.cuda.is_available', return_value=False):
         self.service = FileExtractorService()
   
   @patch('app.services.extraction_service.FileExtractorService._smoldocling_extract')
   def test_extract_text_image(self, mock_extract):
      # Setup
      mock_extract.return_value = "extracted image text"
      
      # Execute
      result = self.service.extract_text("http://localhost:9000/pdf-files/ade60a1704be4f3d9856a442d48f49d5_Screenshot_20250718_210230.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=minioadmin%2F20250814%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250814T184049Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=bdcc613bbcda866aef68a82eebde599edaebcdfa262c51f04ea9a16baacf7d7a")
      
      # Verify
      mock_extract.assert_called_once_with("http://localhost:9000/pdf-files/ade60a1704be4f3d9856a442d48f49d5_Screenshot_20250718_210230.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=minioadmin%2F20250814%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250814T184049Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=bdcc613bbcda866aef68a82eebde599edaebcdfa262c51f04ea9a16baacf7d7a")
      self.assertEqual(result, "extracted image text")
   
   @patch('app.services.extraction_service.fitz.open')
   @patch('app.services.extraction_service.FileExtractorService._smoldocling_extract')
   @patch('builtins.open', new_callable=mock_open)
   @patch('os.remove')
   def test_extract_text_pdf(self, mock_remove, mock_file_open, mock_extract, mock_fitz_open):
      # Setup
      mock_doc = MagicMock()
      mock_page = MagicMock()
      mock_page.get_text.return_value = "pdf text content"
      mock_page.get_images.return_value = [(1, None, None, None, None, None)]  # xref, etc.
      mock_doc.__len__.return_value = 1
      mock_doc.__getitem__.return_value = mock_page
      mock_doc.extract_image.return_value = {"image": b"image_data"}
      mock_fitz_open.return_value = mock_doc
      mock_extract.return_value = "extracted pdf image text"
      
      # Execute
      result = self.service.extract_text("test.pdf")
      
      # Verify
      mock_fitz_open.assert_called_once_with("test.pdf")
      self.assertEqual(mock_page.get_text.call_count, 1)
      mock_extract.assert_called_once()
      mock_file_open.assert_called_once()
      mock_remove.assert_called_once()
      self.assertEqual(result, "pdf text content\n\nextracted pdf image text")
   
   @patch('app.services.extraction_service.DocxDocument')
   def test_extract_text_docx(self, mock_docx):
      # Setup
      mock_doc = MagicMock()
      mock_paragraph1 = MagicMock()
      mock_paragraph1.text = "Paragraph 1"
      mock_paragraph2 = MagicMock()
      mock_paragraph2.text = "Paragraph 2"
      mock_doc.paragraphs = [mock_paragraph1, mock_paragraph2]
      
      mock_table = MagicMock()
      mock_cell1 = MagicMock()
      mock_cell1.text = "Cell 1"
      mock_cell2 = MagicMock()
      mock_cell2.text = "Cell 2"
      mock_row = MagicMock()
      mock_row.cells = [mock_cell1, mock_cell2]
      mock_table.rows = [mock_row]
      mock_doc.tables = [mock_table]
      
      mock_docx.return_value = mock_doc
      
      # Execute
      result = self.service.extract_text("test.docx")
      
      # Verify
      mock_docx.assert_called_once_with("test.docx")
      self.assertEqual(result, "Paragraph 1\nParagraph 2\nCell 1\tCell 2")
   
   @patch('app.services.extraction_service.pd.read_csv')
   def test_extract_text_csv(self, mock_read_csv):
      # Setup
      mock_df = MagicMock()
      mock_df.to_string.return_value = "col1 col2\nval1 val2"
      mock_read_csv.return_value = mock_df
      
      # Execute
      result = self.service.extract_text("test.csv")
      
      # Verify
      mock_read_csv.assert_called_once_with("test.csv")
      mock_df.to_string.assert_called_once_with(index=False)
      self.assertEqual(result, "col1 col2\nval1 val2")
   
   @patch('app.services.extraction_service.pd.read_excel')
   def test_extract_text_excel(self, mock_read_excel):
      # Setup
      mock_df = MagicMock()
      mock_df.to_string.return_value = "col1 col2\nval1 val2"
      mock_read_excel.return_value = {"Sheet1": mock_df}
      
      # Execute
      result = self.service.extract_text("test.xlsx")
      
      # Verify
      mock_read_excel.assert_called_once_with("test.xlsx", sheet_name=None)
      mock_df.to_string.assert_called_once_with(index=False)
      self.assertEqual(result, "--- Sheet: Sheet1 ---\ncol1 col2\nval1 val2")
   
   def test_extract_text_unsupported_format(self):
      # Test with an unsupported file format
      result = self.service.extract_text("test.unsupported")
      self.assertIsNone(result)
   
   def test_extract_text_file_not_found(self):
      # Test with a file that doesn't exist
      result = self.service.extract_text("nonexistent_file.pdf")
      self.assertIsNone(result)

if __name__ == "__main__":
   unittest.main()
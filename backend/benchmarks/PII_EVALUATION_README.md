# PII Evaluation System

Hệ thống đánh giá hiệu suất PII Detection và Unmasking cho AI Guardian với Ground Truth validation.

## 📁 Files

- `accurate_pii_evaluation.py`: Script đánh giá chính với Ground Truth
- `generate_test_data.py`: Tạo dữ liệu test CSV
- `requirements_evaluation.txt`: Dependencies bổ sung
- `FINAL_ACCURACY_REPORT.md`: Báo cáo phân tích chi tiết

## 🚀 Cách sử dụng

### Bước 1: Cài đặt dependencies

```bash
cd backend
pip install -r requirements_evaluation.txt
```

### Bước 2: Chạy đánh giá

#### 🚀 Quick Test (Nhanh - 2-3 phút):
```bash
python accurate_pii_evaluation.py quick
```
- 50 records, 25 detection samples, 10 masking samples
- Phù hợp cho development và debugging

#### 📊 Standard Test (Cân bằng - 5-10 phút):
```bash
python accurate_pii_evaluation.py
```
- 500 records, 200 detection samples, 50 masking samples  
- Tốt cho đánh giá thường xuyên

#### 🎯 Comprehensive Test (Tin cậy cao - 15-30 phút):
```bash
python accurate_pii_evaluation.py comprehensive
```
- 1000 records, 500 detection samples, 100 masking samples
- Độ tin cậy thống kê cao nhất

### Tạo dữ liệu test riêng:
```bash
python generate_test_data.py
```

## 📊 Tính năng đánh giá

### 1. Ground Truth Dataset:
- ✅ Dữ liệu có PII được đánh dấu sẵn
- ✅ Biết chính xác đâu là PII thật, đâu không
- ✅ Phân loại nhiều loại PII: Person, Email, Phone, Credit Card, SSN

### 2. Smart Filtering:
- ✅ Loại bỏ False Positives (InvoiceNo, StockCode nhầm là Driver License)
- ✅ Confidence threshold filtering (score < 0.5)
- ✅ Context-aware detection (bỏ qua date trong InvoiceDate)

### 3. Precision Metrics:
- **Precision**: Tỷ lệ phát hiện đúng trong số các phát hiện
- **Recall**: Tỷ lệ phát hiện được trong số PII thật có
- **F1-Score**: Điểm tổng hợp cân bằng
- **Perfect Roundtrip Rate**: Tỷ lệ unmask thành công hoàn hảo

## 🎯 Kết quả mẫu

### Standard Test (200 detection samples):
```
🎯 PII Performance Evaluation System (Final)
============================================================

🔍 PII DETECTION ACCURACY (Filtered):
   Precision:  0.925 (92.5%)
   Recall:     0.804 (80.4%)
   F1-Score:   0.860 (86.0%)
   ✅ True Positives:  74
   ❌ False Positives: 6
   ⚠️  False Negatives: 18

📈 FILTERING IMPROVEMENT:
   Raw Precision:      0.333 (33.3%)
   Filtered Precision: 1.000 (100.0%)
   Improvement:        +200.0%

🔒 MASKING/UNMASKING ACCURACY:
   Perfect Roundtrip Rate:  0.0% (Needs improvement)
   
🏆 OVERALL SYSTEM SCORE: 43.0%

📊 STATISTICAL RELIABILITY:
   Total Detection Samples: 200
   Total Masking Samples: 50
   Confidence Level: High
   ✅ Large sample size - high statistical reliability
```

### Comprehensive Test (500 detection samples):
- Độ tin cậy thống kê cao hơn
- Phát hiện edge cases hiếm
- Kết quả ổn định hơn qua nhiều lần chạy

## 📁 Output Files

- `accurate_pii_evaluation.json`: Kết quả đánh giá chi tiết
- `labeled_dataset.json`: Sample dataset với ground truth
- `*.csv`: Dữ liệu test được tạo

## 🔧 Customization

### Thay đổi entities được đánh giá:
```python
self.relevant_entities = [
    'PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER', 
    'CREDIT_CARD', 'US_SSN', 'IBAN_CODE'
]
```

### Điều chỉnh confidence threshold:
```python
self.min_confidence = 0.5  # Tăng để giảm False Positives
```

### Thay đổi sample size:
```python
# Trong main()
detection_results = await evaluator.evaluate_with_ground_truth(records, ground_truth, sample_size=100)
masking_results = await evaluator.evaluate_masking_accuracy(records, sample_size=50)
```

## 🚨 Lưu ý

1. **Database**: Đảm bảo database đang chạy cho masking operations
2. **Environment**: Cấu hình `.env` với các keys cần thiết  
3. **Memory**: Script có thể tốn memory với dataset lớn

## 🎯 Ý nghĩa Metrics

- **Precision cao**: Ít False Positives (phát hiện đúng những gì phát hiện)
- **Recall cao**: Ít False Negatives (không bỏ sót PII thật)
- **F1-Score cao**: Cân bằng tốt giữa Precision và Recall
- **Perfect Roundtrip**: Unmask hoàn hảo giống text gốc

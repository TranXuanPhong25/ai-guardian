# PII Evaluation Tools

Bộ công cụ đánh giá hiệu suất PII Detection và Unmasking cho AI Guardian.

## 📁 Files

- `generate_test_data.py`: Tạo dữ liệu test CSV với PII
- `simple_pii_evaluation.py`: Đánh giá đơn giản và nhanh chóng
- `evaluate_pii_performance.py`: Đánh giá chi tiết và toàn diện
- `requirements_evaluation.txt`: Dependencies bổ sung cho evaluation

## 🚀 Cách sử dụng

### Bước 1: Cài đặt dependencies

```bash
cd backend
pip install -r requirements_evaluation.txt
```

### Bước 2: Tạo dữ liệu test

```bash
python generate_test_data.py
```

Lệnh này sẽ tạo ra 2 file:
- `simple_test_data.csv`: Dữ liệu cơ bản theo format yêu cầu
- `complex_test_data_with_pii.csv`: Dữ liệu mở rộng với nhiều PII

### Bước 3: Chạy đánh giá

#### Đánh giá nhanh (khuyến nghị):
```bash
python simple_pii_evaluation.py
```

#### Đánh giá chi tiết:
```bash
python evaluate_pii_performance.py
```

## 📊 Kết quả đánh giá

### Metrics đo lường:

1. **Detection Performance**:
   - Số lượng PII entities được phát hiện
   - Trung bình entities per record
   - Chi tiết các loại PII được detect

2. **Masking Performance**:
   - Tỷ lệ masking thành công (%)
   - Tỷ lệ unmasking thành công (%)
   - Tỷ lệ thành công tổng thể (%)

### Output files:
- `evaluation_results.json`: Kết quả đánh giá chi tiết
- `pii_performance_report.json`: Báo cáo toàn diện (nếu dùng script chi tiết)

## 🎯 Ví dụ kết quả

```
📊 PII EVALUATION SUMMARY
============================================================

🔍 DETECTION ANALYSIS:
   Records processed: 50
   Total PII entities detected: 85
   Average entities per record: 1.70

🔒 MASKING/UNMASKING ANALYSIS:
   Records processed: 20
   Successful masks: 18
   Successful unmasks: 17
   Masking success rate: 90.0%
   Unmasking success rate: 94.4%
   Overall success rate: 85.0%
```

## 🔧 Customization

### Thay đổi sample size:
Sửa trong `simple_pii_evaluation.py`:
```python
detection_results = await evaluator.test_detection_rate(records, sample_size=100)
masking_results = await evaluator.test_masking_unmasking(records, sample_size=50)
```

### Thêm loại PII khác:
Sửa trong `generate_test_data.py` để thêm các loại PII mới:
```python
# Thêm IP address
if random.random() < 0.1:
    record['IPAddress'] = fake.ipv4()
```

### Thay đổi entities được detect:
Sửa trong evaluator, thêm vào `analyze()`:
```python
analysis_results = self.masker.analyzer.analyze(
    text=text,
    language='en',
    entities=['PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER', 'CREDIT_CARD', 'US_SSN']
)
```

## 🚨 Lưu ý

1. **Database**: Đảm bảo database đang chạy khi test unmasking (để lưu mappings)
2. **Environment**: Cấu hình `.env` file với các keys cần thiết
3. **Memory**: Script chi tiết có thể tốn nhiều memory với dataset lớn
4. **Performance**: Test với sample nhỏ trước khi chạy full dataset

## 🐛 Troubleshooting

### Lỗi import services:
```bash
# Đảm bảo chạy từ thư mục backend
cd backend
python simple_pii_evaluation.py
```

### Lỗi database connection:
- Kiểm tra database đang chạy
- Kiểm tra `DATABASE_URL` trong `.env`
- Chạy migrations: `alembic upgrade head`

### Lỗi thiếu dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements_evaluation.txt
```

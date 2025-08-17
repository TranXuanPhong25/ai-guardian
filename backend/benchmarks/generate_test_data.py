#!/usr/bin/env python3
"""
Script tạo dữ liệu test CSV với PII cho việc đánh giá hiệu suất
Tạo file CSV với format như yêu cầu và có chứa các loại PII khác nhau
"""

import csv
import random
from datetime import datetime, timedelta
from faker import Faker


def generate_test_csv(filename: str = "test_data_with_pii.csv", num_records: int = 1000):
    """
    Tạo file CSV test với PII theo format yêu cầu
    """
    fake = Faker(['en_US', 'vi_VN'])
    
    # Header như trong ví dụ
    fieldnames = ['InvoiceNo', 'StockCode', 'Description', 'Quantity', 'InvoiceDate', 'UnitPrice', 'CustomerID', 'Country']
    
    # Thêm thêm một số field có thể chứa PII
    extended_fieldnames = fieldnames + ['CustomerName', 'CustomerEmail', 'CustomerPhone', 'Notes']
    
    print(f"Generating {num_records} records...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=extended_fieldnames)
        writer.writeheader()
        
        for i in range(num_records):
            # Base data theo format gốc
            record = {
                'InvoiceNo': 536365 + i,
                'StockCode': f"P{random.randint(1000, 9999)}",
                'Description': random.choice(['LIKE', 'PRESENT', 'GIFT', 'ITEM', 'PRODUCT', 'BOOK', 'TOY']),
                'Quantity': random.randint(1, 50),
                'InvoiceDate': fake.date_time_between(start_date='-1y', end_date='now').strftime('%Y-%m-%d %H:%M:%S'),
                'UnitPrice': round(random.uniform(1.0, 100.0), 2),
                'CustomerID': random.randint(10000, 99999),
                'Country': fake.country()
            }
            
            # Thêm PII vào các field mở rộng với xác suất khác nhau
            
            # 40% chance có tên khách hàng
            if random.random() < 0.4:
                record['CustomerName'] = fake.name()
            else:
                record['CustomerName'] = ''
            
            # 30% chance có email
            if random.random() < 0.3:
                record['CustomerEmail'] = fake.email()
            else:
                record['CustomerEmail'] = ''
            
            # 25% chance có số điện thoại
            if random.random() < 0.25:
                record['CustomerPhone'] = fake.phone_number()
            else:
                record['CustomerPhone'] = ''
            
            # 20% chance có notes với PII mixed
            if random.random() < 0.2:
                notes_parts = []
                
                # Có thể chứa tên người
                if random.random() < 0.5:
                    notes_parts.append(f"Contact: {fake.name()}")
                
                # Có thể chứa số thẻ tín dụng
                if random.random() < 0.3:
                    notes_parts.append(f"Card ending: ****{fake.credit_card_number()[-4:]}")
                
                # Có thể chứa địa chỉ
                if random.random() < 0.4:
                    notes_parts.append(f"Ship to: {fake.address().replace('\n', ', ')}")
                
                # Có thể chứa SSN
                if random.random() < 0.1:
                    notes_parts.append(f"SSN: {fake.ssn()}")
                
                record['Notes'] = " | ".join(notes_parts) if notes_parts else "Standard order"
            else:
                record['Notes'] = ''
            
            # Đôi khi thêm PII vào Description
            if random.random() < 0.15:
                record['Description'] = f"{record['Description']} for {fake.first_name()}"
            
            writer.writerow(record)
    
    print(f"✅ Test data saved to {filename}")
    print(f"📊 Generated {num_records} records with mixed PII data")
    

def generate_simple_csv(filename: str = "simple_test_data.csv", num_records: int = 100):
    """
    Tạo file CSV đơn giản theo đúng format ví dụ
    """
    fake = Faker()
    
    print(f"Generating {num_records} simple records...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Header theo ví dụ
        writer.writerow(['InvoiceNo', 'StockCode', 'Description', 'Quantity', 'InvoiceDate', 'UnitPrice', 'CustomerID', 'Country'])
        
        for i in range(num_records):
            row = [
                536365 + i,
                f"P{random.randint(1000, 9999)}",
                random.choice(['LIKE', 'PRESENT', 'GIFT', 'ITEM']),
                random.randint(1, 50),
                fake.date_time_between(start_date='-1y', end_date='now').strftime('%Y-%m-%d %H:%M:%S'),
                round(random.uniform(1.0, 100.0), 2),
                random.randint(10000, 99999),
                fake.country()
            ]
            writer.writerow(row)
    
    print(f"✅ Simple test data saved to {filename}")


if __name__ == "__main__":
    print("🔧 CSV Test Data Generator")
    print("=" * 50)
    
    # Tạo file CSV đơn giản theo format ví dụ
    generate_simple_csv("simple_test_data.csv", 100)
    
    print()
    
    # Tạo file CSV phức tạp với nhiều PII
    generate_test_csv("complex_test_data_with_pii.csv", 500)
    
    print("\n🎯 Generated test files:")
    print("  - simple_test_data.csv: Basic format as example")
    print("  - complex_test_data_with_pii.csv: Extended format with PII data")

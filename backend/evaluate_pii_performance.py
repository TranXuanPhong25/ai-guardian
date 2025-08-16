#!/usr/bin/env python3
"""
Script đánh giá hiệu suất PII Detection và Unmasking Service
- Tạo dữ liệu test CSV với PII
- Đánh giá tỷ lệ detect đúng của Presidio 
- Đánh giá tỷ lệ unmask thành công
- Báo cáo chi tiết hiệu suất
"""

import csv
import json
import os
import random
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Set
import pandas as pd
from faker import Faker
import asyncio

# Thêm path để import các service
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.masking_service import PIIMaskerService
from app.services.unmasking_service import PIIUnmaskerService


class PIIPerformanceEvaluator:
    """Class đánh giá hiệu suất PII Detection và Unmasking"""
    
    def __init__(self):
        self.faker = Faker(['en_US', 'vi_VN'])
        self.masker = PIIMaskerService()
        self.unmasker = PIIUnmaskerService()
        
        # Định nghĩa các loại PII và pattern tương ứng
        self.pii_types = {
            'PERSON': 'person_name',
            'EMAIL_ADDRESS': 'email',
            'PHONE_NUMBER': 'phone_number',
            'CREDIT_CARD': 'credit_card_number',
            'US_SSN': 'ssn',
            'DATE_TIME': 'date_time',
            'IP_ADDRESS': 'ipv4',
            'IBAN_CODE': 'iban',
            'US_DRIVER_LICENSE': 'license_plate'
        }
        
    def generate_test_data(self, num_records: int = 1000) -> Tuple[List[Dict], Set[Tuple]]:
        """
        Tạo dữ liệu test CSV với PII
        Returns:
            - List of records
            - Set of expected PII (entity_type, value) tuples
        """
        records = []
        expected_pii = set()
        
        print(f"Generating {num_records} test records...")
        
        for i in range(num_records):
            # Tạo dữ liệu cơ bản
            record = {
                'InvoiceNo': f"{536365 + i}",
                'StockCode': f"P{random.randint(1000, 9999)}",
                'Description': random.choice(['LIKE', 'PRESENT', 'GIFT', 'ITEM', 'PRODUCT']),
                'Quantity': random.randint(1, 50),
                'InvoiceDate': self.faker.date_time_between(start_date='-1y', end_date='now').strftime('%Y-%m-%d %H:%M:%S'),
                'UnitPrice': round(random.uniform(1.0, 100.0), 2),
                'Country': self.faker.country()
            }
            
            # Thêm PII vào một số field ngẫu nhiên
            if random.random() < 0.3:  # 30% chance có tên người
                person_name = self.faker.name()
                record['Description'] = f"{record['Description']} for {person_name}"
                expected_pii.add(('PERSON', person_name))
            
            if random.random() < 0.2:  # 20% chance có email
                email = self.faker.email()
                record['CustomerEmail'] = email
                expected_pii.add(('EMAIL_ADDRESS', email))
            
            if random.random() < 0.25:  # 25% chance có phone
                phone = self.faker.phone_number()
                record['CustomerPhone'] = phone
                expected_pii.add(('PHONE_NUMBER', phone))
            
            if random.random() < 0.15:  # 15% chance có credit card
                cc = self.faker.credit_card_number()
                record['PaymentCard'] = cc
                expected_pii.add(('CREDIT_CARD', cc))
            
            # Thêm CustomerID thực (có thể là PII)
            customer_id = random.randint(10000, 99999)
            record['CustomerID'] = customer_id
            
            records.append(record)
        
        return records, expected_pii
    
    def save_test_data_to_csv(self, records: List[Dict], filename: str = "test_data.csv"):
        """Lưu dữ liệu test vào file CSV"""
        if not records:
            return
            
        fieldnames = records[0].keys()
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        
        print(f"Test data saved to {filename}")
    
    def flatten_record_text(self, record: Dict) -> str:
        """Chuyển đổi record thành text để test PII detection"""
        text_parts = []
        for key, value in record.items():
            if isinstance(value, str):
                text_parts.append(f"{key}: {value}")
            else:
                text_parts.append(f"{key}: {str(value)}")
        return " | ".join(text_parts)
    
    async def evaluate_detection_rate(self, records: List[Dict], expected_pii: Set[Tuple]) -> Dict:
        """Đánh giá tỷ lệ detect đúng của Presidio"""
        print("Evaluating PII detection rate...")
        
        detected_pii = set()
        total_texts = len(records)
        detection_results = []
        
        for i, record in enumerate(records):
            if i % 100 == 0:
                print(f"Processing record {i+1}/{total_texts}")
            
            text = self.flatten_record_text(record)
            
            try:
                # Analyze text với Presidio
                analysis_results = self.masker.analyzer.analyze(
                    text=text,
                    language='en',
                    entities=list(self.pii_types.keys())
                )
                
                # Extract detected entities
                for result in analysis_results:
                    entity_text = text[result.start:result.end]
                    detected_pii.add((result.entity_type, entity_text))
                    
                detection_results.append({
                    'record_id': i,
                    'text': text,
                    'detected_entities': [(r.entity_type, text[r.start:r.end], r.score) for r in analysis_results]
                })
                
            except Exception as e:
                print(f"Error processing record {i}: {e}")
                continue
        
        # Tính toán metrics
        true_positives = len(detected_pii.intersection(expected_pii))
        false_positives = len(detected_pii - expected_pii)
        false_negatives = len(expected_pii - detected_pii)
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'total_expected': len(expected_pii),
            'total_detected': len(detected_pii),
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'detection_results': detection_results,
            'expected_pii': list(expected_pii),
            'detected_pii': list(detected_pii)
        }
    
    async def evaluate_masking_unmasking(self, records: List[Dict]) -> Dict:
        """Đánh giá tỷ lệ masking và unmasking thành công"""
        print("Evaluating masking and unmasking performance...")
        
        masking_results = []
        successful_masks = 0
        successful_unmasks = 0
        total_processed = 0
        
        for i, record in enumerate(records[:100]):  # Test với 100 records đầu
            if i % 20 == 0:
                print(f"Processing masking/unmasking for record {i+1}/100")
            
            text = self.flatten_record_text(record)
            original_text = text
            
            try:
                # Step 1: Mask the text
                masked_result = await self.masker.mask_text(text)
                # mask_text() returns (masked_text, mapping) tuple
                masked_text, mappings = masked_result
                
                masking_success = masked_text != original_text and len(mappings) > 0
                if masking_success:
                    successful_masks += 1
                
                # Step 2: Unmask the text
                if masking_success:
                    # mappings is already a dict from pseudonym -> original_value
                    unmasked_text = self.unmasker.unmask_text(masked_text, mappings)
                    
                    # Check if unmasking was successful
                    unmasking_success = unmasked_text == original_text
                    if unmasking_success:
                        successful_unmasks += 1
                else:
                    unmasked_text = masked_text
                    unmasking_success = False
                
                masking_results.append({
                    'record_id': i,
                    'original_text': original_text,
                    'masked_text': masked_text,
                    'unmasked_text': unmasked_text,
                    'mappings': mappings,
                    'masking_success': masking_success,
                    'unmasking_success': unmasking_success,
                    'entities_detected': len(mappings)
                })
                
                total_processed += 1
                
            except Exception as e:
                print(f"Error in masking/unmasking record {i}: {e}")
                masking_results.append({
                    'record_id': i,
                    'error': str(e),
                    'masking_success': False,
                    'unmasking_success': False
                })
                continue
        
        # Tính toán metrics
        masking_success_rate = successful_masks / total_processed if total_processed > 0 else 0
        unmasking_success_rate = successful_unmasks / successful_masks if successful_masks > 0 else 0
        overall_success_rate = successful_unmasks / total_processed if total_processed > 0 else 0
        
        return {
            'total_processed': total_processed,
            'successful_masks': successful_masks,
            'successful_unmasks': successful_unmasks,
            'masking_success_rate': masking_success_rate,
            'unmasking_success_rate': unmasking_success_rate,
            'overall_success_rate': overall_success_rate,
            'detailed_results': masking_results
        }
    
    def generate_report(self, detection_metrics: Dict, masking_metrics: Dict, output_file: str = "pii_performance_report.json"):
        """Tạo báo cáo tổng hợp"""
        timestamp = datetime.now().isoformat()
        
        report = {
            'evaluation_timestamp': timestamp,
            'detection_performance': {
                'precision': detection_metrics['precision'],
                'recall': detection_metrics['recall'],
                'f1_score': detection_metrics['f1_score'],
                'total_expected_pii': detection_metrics['total_expected'],
                'total_detected_pii': detection_metrics['total_detected'],
                'true_positives': detection_metrics['true_positives'],
                'false_positives': detection_metrics['false_positives'],
                'false_negatives': detection_metrics['false_negatives']
            },
            'masking_performance': {
                'masking_success_rate': masking_metrics['masking_success_rate'],
                'unmasking_success_rate': masking_metrics['unmasking_success_rate'],
                'overall_success_rate': masking_metrics['overall_success_rate'],
                'total_processed': masking_metrics['total_processed'],
                'successful_masks': masking_metrics['successful_masks'],
                'successful_unmasks': masking_metrics['successful_unmasks']
            },
            'detailed_analysis': {
                'expected_pii_samples': detection_metrics['expected_pii'][:10],  # First 10 samples
                'detected_pii_samples': detection_metrics['detected_pii'][:10],
                'masking_examples': masking_metrics['detailed_results'][:5]  # First 5 examples
            }
        }
        
        # Save to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        return report
    
    def print_summary(self, report: Dict):
        """In tóm tắt kết quả"""
        print("\n" + "="*60)
        print("PII PERFORMANCE EVALUATION SUMMARY")
        print("="*60)
        
        # Detection Performance
        detection = report['detection_performance']
        print(f"\n📊 PII DETECTION PERFORMANCE:")
        print(f"   Precision: {detection['precision']:.3f} ({detection['precision']*100:.1f}%)")
        print(f"   Recall:    {detection['recall']:.3f} ({detection['recall']*100:.1f}%)")
        print(f"   F1-Score:  {detection['f1_score']:.3f} ({detection['f1_score']*100:.1f}%)")
        print(f"   Expected PII: {detection['total_expected_pii']}")
        print(f"   Detected PII: {detection['total_detected_pii']}")
        print(f"   True Positives: {detection['true_positives']}")
        print(f"   False Positives: {detection['false_positives']}")
        print(f"   False Negatives: {detection['false_negatives']}")
        
        # Masking Performance
        masking = report['masking_performance']
        print(f"\n🔒 MASKING/UNMASKING PERFORMANCE:")
        print(f"   Masking Success Rate:   {masking['masking_success_rate']:.3f} ({masking['masking_success_rate']*100:.1f}%)")
        print(f"   Unmasking Success Rate: {masking['unmasking_success_rate']:.3f} ({masking['unmasking_success_rate']*100:.1f}%)")
        print(f"   Overall Success Rate:   {masking['overall_success_rate']:.3f} ({masking['overall_success_rate']*100:.1f}%)")
        print(f"   Total Processed: {masking['total_processed']}")
        print(f"   Successful Masks: {masking['successful_masks']}")
        print(f"   Successful Unmasks: {masking['successful_unmasks']}")
        
        print(f"\n📋 Report saved to: pii_performance_report.json")
        print("="*60)


async def main():
    """Chương trình chính"""
    print("🚀 Starting PII Performance Evaluation...")
    
    evaluator = PIIPerformanceEvaluator()
    
    # Step 1: Generate test data
    print("\n1. Generating test data...")
    records, expected_pii = evaluator.generate_test_data(num_records=500)
    evaluator.save_test_data_to_csv(records, "pii_test_data.csv")
    
    # Step 2: Evaluate detection rate
    print("\n2. Evaluating PII detection performance...")
    detection_metrics = await evaluator.evaluate_detection_rate(records, expected_pii)
    
    # Step 3: Evaluate masking/unmasking
    print("\n3. Evaluating masking/unmasking performance...")
    masking_metrics = await evaluator.evaluate_masking_unmasking(records)
    
    # Step 4: Generate report
    print("\n4. Generating performance report...")
    report = evaluator.generate_report(detection_metrics, masking_metrics)
    
    # Step 5: Print summary
    evaluator.print_summary(report)
    
    print("\n✅ Evaluation completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())

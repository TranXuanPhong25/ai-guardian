#!/usr/bin/env python3
"""
Script đánh giá đơn giản cho PII Detection và Unmasking
Đọc dữ liệu từ file CSV và đánh giá hiệu suất
"""

import csv
import json
import os
import sys
import asyncio
from typing import Dict, List
from datetime import datetime

# Add path to import services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.services.masking_service import PIIMaskerService
    from app.services.unmasking_service import PIIUnmaskerService
except ImportError as e:
    print(f"Error importing services: {e}")
    print("Please make sure you're running this from the backend directory")
    sys.exit(1)


class SimpleEvaluator:
    """Simple evaluator for PII services"""
    
    def __init__(self):
        self.masker = PIIMaskerService()
        self.unmasker = PIIUnmaskerService()
    
    def read_csv_data(self, filename: str) -> List[Dict]:
        """Đọc dữ liệu từ file CSV"""
        records = []
        try:
            with open(filename, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    records.append(row)
            print(f"✅ Loaded {len(records)} records from {filename}")
        except FileNotFoundError:
            print(f"❌ File {filename} not found")
        except Exception as e:
            print(f"❌ Error reading CSV: {e}")
        
        return records
    
    def record_to_text(self, record: Dict) -> str:
        """Chuyển đổi record thành text"""
        text_parts = []
        for key, value in record.items():
            if value:  # Only include non-empty values
                text_parts.append(f"{key}: {value}")
        return " | ".join(text_parts)
    
    async def test_detection_rate(self, records: List[Dict], sample_size: int = 50) -> Dict:
        """Test tỷ lệ phát hiện PII"""
        print(f"\n🔍 Testing PII detection on {sample_size} samples...")
        
        detection_results = []
        total_entities_detected = 0
        
        for i, record in enumerate(records[:sample_size]):
            text = self.record_to_text(record)
            
            try:
                # Analyze with Presidio
                analysis_results = self.masker.analyzer.analyze(
                    text=text,
                    language='en'
                )
                
                entities = []
                for result in analysis_results:
                    entity_text = text[result.start:result.end]
                    entities.append({
                        'type': result.entity_type,
                        'text': entity_text,
                        'score': result.score,
                        'start': result.start,
                        'end': result.end
                    })
                
                total_entities_detected += len(entities)
                
                detection_results.append({
                    'record_id': i,
                    'original_text': text,
                    'entities_found': len(entities),
                    'entities': entities
                })
                
                if (i + 1) % 10 == 0:
                    print(f"  Processed {i + 1}/{sample_size} records")
                    
            except Exception as e:
                print(f"  ❌ Error processing record {i}: {e}")
                continue
        
        avg_entities_per_record = total_entities_detected / len(detection_results) if detection_results else 0
        
        return {
            'total_records_processed': len(detection_results),
            'total_entities_detected': total_entities_detected,
            'avg_entities_per_record': avg_entities_per_record,
            'detection_results': detection_results
        }
    
    async def test_masking_unmasking(self, records: List[Dict], sample_size: int = 20) -> Dict:
        """Test tỷ lệ masking và unmasking thành công"""
        print(f"\n🔒 Testing masking/unmasking on {sample_size} samples...")
        
        results = []
        successful_masks = 0
        successful_unmasks = 0
        
        for i, record in enumerate(records[:sample_size]):
            text = self.record_to_text(record)
            
            try:
                print(f"  Processing record {i + 1}/{sample_size}")
                
                # Step 1: Mask the text
                masked_result = await self.masker.mask_text(text)
                # mask_text() returns (masked_text, mapping) tuple
                masked_text, mappings = masked_result
                
                # Check if masking was successful (text changed and mappings exist)
                masking_successful = (masked_text != text) and bool(mappings)
                if masking_successful:
                    successful_masks += 1
                
                # Step 2: Unmask if masking was successful
                unmasking_successful = False
                unmasked_text = masked_text
                
                if masking_successful:
                    # mappings is already a dict from pseudonym -> original_value
                    if mappings:
                        unmasked_text = self.unmasker.unmask_text(masked_text, mappings)
                        unmasking_successful = (unmasked_text == text)
                        if unmasking_successful:
                            successful_unmasks += 1
                
                results.append({
                    'record_id': i,
                    'original_text': text[:200] + "..." if len(text) > 200 else text,
                    'masked_text': masked_text[:200] + "..." if len(masked_text) > 200 else masked_text,
                    'unmasked_text': unmasked_text[:200] + "..." if len(unmasked_text) > 200 else unmasked_text,
                    'entities_found': len(mappings),  # mappings is now a simple dict
                    'masking_successful': masking_successful,
                    'unmasking_successful': unmasking_successful,
                    'mappings_count': len(mappings)
                })
                
            except Exception as e:
                print(f"  ❌ Error processing record {i}: {e}")
                results.append({
                    'record_id': i,
                    'error': str(e),
                    'masking_successful': False,
                    'unmasking_successful': False
                })
        
        total_processed = len([r for r in results if 'error' not in r])
        masking_rate = successful_masks / total_processed if total_processed > 0 else 0
        unmasking_rate = successful_unmasks / successful_masks if successful_masks > 0 else 0
        overall_rate = successful_unmasks / total_processed if total_processed > 0 else 0
        
        return {
            'total_processed': total_processed,
            'successful_masks': successful_masks,
            'successful_unmasks': successful_unmasks,
            'masking_success_rate': masking_rate,
            'unmasking_success_rate': unmasking_rate,
            'overall_success_rate': overall_rate,
            'detailed_results': results
        }
    
    def save_results(self, detection_results: Dict, masking_results: Dict, filename: str = "evaluation_results.json"):
        """Lưu kết quả đánh giá"""
        timestamp = datetime.now().isoformat()
        
        report = {
            'timestamp': timestamp,
            'detection_analysis': {
                'total_records_processed': detection_results['total_records_processed'],
                'total_entities_detected': detection_results['total_entities_detected'],
                'avg_entities_per_record': detection_results['avg_entities_per_record'],
                'sample_results': detection_results['detection_results'][:5]  # First 5 samples
            },
            'masking_analysis': {
                'total_processed': masking_results['total_processed'],
                'successful_masks': masking_results['successful_masks'],
                'successful_unmasks': masking_results['successful_unmasks'],
                'masking_success_rate': masking_results['masking_success_rate'],
                'unmasking_success_rate': masking_results['unmasking_success_rate'],
                'overall_success_rate': masking_results['overall_success_rate'],
                'sample_results': masking_results['detailed_results'][:5]  # First 5 samples
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📊 Results saved to {filename}")
        return report
    
    def print_summary(self, detection_results: Dict, masking_results: Dict):
        """In tóm tắt kết quả"""
        print("\n" + "="*60)
        print("📊 PII EVALUATION SUMMARY")
        print("="*60)
        
        # Detection Summary
        print(f"\n🔍 DETECTION ANALYSIS:")
        print(f"   Records processed: {detection_results['total_records_processed']}")
        print(f"   Total PII entities detected: {detection_results['total_entities_detected']}")
        print(f"   Average entities per record: {detection_results['avg_entities_per_record']:.2f}")
        
        # Masking Summary
        print(f"\n🔒 MASKING/UNMASKING ANALYSIS:")
        print(f"   Records processed: {masking_results['total_processed']}")
        print(f"   Successful masks: {masking_results['successful_masks']}")
        print(f"   Successful unmasks: {masking_results['successful_unmasks']}")
        print(f"   Masking success rate: {masking_results['masking_success_rate']:.1%}")
        print(f"   Unmasking success rate: {masking_results['unmasking_success_rate']:.1%}")
        print(f"   Overall success rate: {masking_results['overall_success_rate']:.1%}")
        
        print("\n" + "="*60)


async def main():
    """Main function"""
    print("🚀 Simple PII Evaluation Tool")
    print("="*50)
    
    evaluator = SimpleEvaluator()
    
    # Try to find CSV files
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    if not csv_files:
        print("❌ No CSV files found in current directory")
        print("💡 Run generate_test_data.py first to create test data")
        return
    
    print(f"📁 Found CSV files: {csv_files}")
    
    # Use the first CSV file found
    csv_file = csv_files[0]
    print(f"📊 Using {csv_file} for evaluation")
    
    # Load data
    records = evaluator.read_csv_data(csv_file)
    if not records:
        print("❌ No data loaded, exiting")
        return
    
    # Run detection test
    detection_results = await evaluator.test_detection_rate(records, sample_size=min(50, len(records)))
    
    # Run masking/unmasking test
    masking_results = await evaluator.test_masking_unmasking(records, sample_size=min(20, len(records)))
    
    # Save and display results
    evaluator.save_results(detection_results, masking_results)
    evaluator.print_summary(detection_results, masking_results)
    
    print("\n✅ Evaluation completed!")


if __name__ == "__main__":
    asyncio.run(main())

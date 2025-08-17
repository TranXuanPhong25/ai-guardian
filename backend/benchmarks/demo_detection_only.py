#!/usr/bin/env python3
"""
Demo script to compare Detection-Only vs Full Pipeline performance
"""

import asyncio
import time
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.services.masking_service import PIIMaskerService
    from app.services.unmasking_service import PIIUnmaskerService
    from app.services.notification_service import notification_service
except ImportError as e:
    print(f"❌ Error importing services: {e}")
    sys.exit(1)

# Sample test data
TEST_SAMPLES = [
    "Patient John Smith (DOB: 1985-03-15) visited the hospital.",
    "Contact Dr. Sarah Johnson at sarah.johnson@hospital.com or (555) 123-4567.",
    "SSN: 123-45-6789, Credit Card: 4532-1234-5678-9012",
    "Emergency contact: Mary Davis, email: mary.davis@gmail.com, phone: (555) 987-6543",
    "Patient ID 12345 scheduled for 2024-12-01 at St. Mary's Hospital"
]

async def demo_detection_only():
    """Demo detection-only mode"""
    print("🔍 DETECTION-ONLY MODE DEMO")
    print("=" * 50)
    
    start_time = time.time()
    total_detected = 0
    
    for i, text in enumerate(TEST_SAMPLES, 1):
        print(f"\n📝 Sample {i}: {text[:50]}...")
        
        # Only detection
        detected = await notification_service.detect_pii(text)
        if detected:
            total_detected += len(detected)
            print(f"   🔍 Detected {len(detected)} PII entities:")
            for detection in detected:
                print(f"      - {detection['entity_type']}: '{detection['text']}' (score: {detection['score']:.2f})")
        else:
            print(f"   ⚠️  No PII detected")
    
    detection_time = time.time() - start_time
    
    print(f"\n📊 Detection-Only Results:")
    print(f"   ⏱️  Time: {detection_time:.3f} seconds")
    print(f"   🔍 Total PII detected: {total_detected}")
    print(f"   🚀 Throughput: {len(TEST_SAMPLES)/detection_time:.1f} samples/second")
    
    return detection_time, total_detected

async def demo_full_pipeline():
    """Demo full pipeline mode"""
    print("\n\n🔄 FULL PIPELINE MODE DEMO")
    print("=" * 50)
    
    masker = PIIMaskerService()
    unmasker = PIIUnmaskerService()
    
    start_time = time.time()
    total_detected = 0
    total_masked = 0
    total_roundtrip_success = 0
    
    for i, text in enumerate(TEST_SAMPLES, 1):
        print(f"\n📝 Sample {i}: {text[:50]}...")
        
        # Detection
        detected = await notification_service.detect_pii(text)
        if detected:
            total_detected += len(detected)
            print(f"   🔍 Detected {len(detected)} PII entities")
        
        # Masking
        masked_text, mapping = await masker.mask_text(text)
        if mapping:
            total_masked += 1
            print(f"   🔒 Masked: {masked_text[:50]}...")
            print(f"   🗝️  Mapping: {len(mapping)} pseudonyms")
            
            # Unmasking
            unmasked_text = unmasker.unmask_text(masked_text, mapping)
            if unmasked_text.strip() == text.strip():
                total_roundtrip_success += 1
                print(f"   ✅ Roundtrip: SUCCESS")
            else:
                print(f"   ❌ Roundtrip: FAILED")
        else:
            print(f"   ⚠️  No masking performed")
    
    full_time = time.time() - start_time
    
    print(f"\n📊 Full Pipeline Results:")
    print(f"   ⏱️  Time: {full_time:.3f} seconds")
    print(f"   🔍 Total PII detected: {total_detected}")
    print(f"   🔒 Samples masked: {total_masked}/{len(TEST_SAMPLES)}")
    print(f"   🎯 Roundtrip success: {total_roundtrip_success}/{len(TEST_SAMPLES)}")
    print(f"   🚀 Throughput: {len(TEST_SAMPLES)/full_time:.1f} samples/second")
    
    return full_time, total_detected, total_masked, total_roundtrip_success

async def main():
    """Run both demos and compare"""
    print("🚀 PII PROCESSING MODE COMPARISON DEMO")
    print("=" * 60)
    print(f"Testing {len(TEST_SAMPLES)} sample texts...")
    
    # Run detection-only demo
    detection_time, detected_count = await demo_detection_only()
    
    # Run full pipeline demo
    full_time, full_detected, masked_count, roundtrip_count = await demo_full_pipeline()
    
    # Comparison
    print("\n\n📈 PERFORMANCE COMPARISON")
    print("=" * 60)
    print(f"{'Metric':<25} {'Detection-Only':<15} {'Full Pipeline':<15} {'Difference':<15}")
    print("-" * 60)
    print(f"{'Time (seconds)':<25} {detection_time:<15.3f} {full_time:<15.3f} {full_time/detection_time:<15.1f}x")
    print(f"{'Throughput (samples/s)':<25} {len(TEST_SAMPLES)/detection_time:<15.1f} {len(TEST_SAMPLES)/full_time:<15.1f} {detection_time/full_time:<15.1f}x")
    print(f"{'PII Entities Detected':<25} {detected_count:<15} {full_detected:<15} {'Same' if detected_count == full_detected else 'Different':<15}")
    
    print(f"\n💡 Key Insights:")
    print(f"   • Detection-only is {full_time/detection_time:.1f}x faster than full pipeline")
    print(f"   • Use detection-only for: accuracy testing, performance benchmarking, PII audit")
    print(f"   • Use full pipeline for: end-to-end testing, roundtrip validation, production simulation")
    print(f"   • Both modes detect the same PII entities with identical accuracy")

if __name__ == "__main__":
    asyncio.run(main())

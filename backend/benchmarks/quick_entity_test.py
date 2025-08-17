#!/usr/bin/env python3
"""
Quick Entity Test - Test nhanh các entity type cơ bản với large dataset
"""

import sys
import os
import asyncio
import random
from typing import Dict, List
from faker import Faker

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.services.masking_service import PIIMaskerService
    from app.services.unmasking_service import PIIUnmaskerService
    from app.services.notification_service import notification_service
except ImportError as e:
    print(f"❌ Error importing services: {e}")
    sys.exit(1)

def generate_test_cases(num_cases: int = 100) -> Dict[str, List[str]]:
    """Generate large number of test cases for each entity type"""
    faker = Faker(['en_US'])  # Only English data
    test_cases = {}
    
    print(f"🔄 Generating {num_cases} test cases for each entity type...")
    
    # PERSON test cases
    person_cases = []
    person_templates = [
        "Patient name: {}",
        "Dr. {} treated the patient", 
        "Contact person: {}",
        "Employee: {}",
        "Customer: {}",
        "The patient {} was admitted",
        "Physician: Dr. {}",
        "Nurse {} is assigned",
        "Staff member: {}",
        "Healthcare worker: {}",
        "Resident: {}",
        "Specialist: Dr. {}",
        "Consultant: {}",
        "Attending physician: {}",
        "Medical resident: {}",
        "Chief of staff: Dr. {}",
        "Therapist: {}",
        "Surgeon: Dr. {}",
        "Anesthesiologist: Dr. {}",
        "Radiologist: Dr. {}"
    ]
    for i in range(num_cases):
        name = faker.name()
        template = random.choice(person_templates)
        person_cases.append(template.format(name))
    test_cases["PERSON"] = person_cases
    
    # EMAIL_ADDRESS test cases
    email_cases = []
    email_templates = [
        "Email: {}",
        "Send report to: {}",
        "Patient email: {}",
        "Contact email: {}",
        "Billing email: {}",
        "Emergency contact: {}",
        "Staff email: {}",
        "Provider email: {}",
        "Insurance contact: {}",
        "Pharmacy email: {}",
        "Lab results to: {}",
        "Report delivery: {}"
    ]
    for i in range(num_cases):
        email = faker.email()
        template = random.choice(email_templates)
        email_cases.append(template.format(email))
    test_cases["EMAIL_ADDRESS"] = email_cases
    
    # PHONE_NUMBER test cases
    phone_cases = []
    phone_templates = [
        "Phone: {}",
        "Emergency contact: {}",
        "Mobile: {}",
        "Office: {}",
        "Home phone: {}",
        "Cell: {}",
        "Contact number: {}",
        "Hospital phone: {}",
        "Clinic number: {}",
        "Insurance phone: {}",
        "Pharmacy: {}",
        "Appointment line: {}"
    ]
    phone_formats = [
        lambda: f"+1-{faker.random_int(100,999)}-{faker.random_int(100,999)}-{faker.random_int(1000,9999)}",
        lambda: f"({faker.random_int(100,999)}) {faker.random_int(100,999)}-{faker.random_int(1000,9999)}",
        lambda: f"{faker.random_int(100,999)}.{faker.random_int(100,999)}.{faker.random_int(1000,9999)}",
        lambda: f"{faker.random_int(100,999)}-{faker.random_int(100,999)}-{faker.random_int(1000,9999)}",
        lambda: faker.phone_number()
    ]
    for i in range(num_cases):
        phone = random.choice(phone_formats)()
        template = random.choice(phone_templates)
        phone_cases.append(template.format(phone))
    test_cases["PHONE_NUMBER"] = phone_cases
    
    # US_SSN test cases
    ssn_cases = []
    ssn_templates = [
        "SSN: {}",
        "Social Security Number: {}",
        "Patient SSN: {}",
        "Employee SSN: {}",
        "Tax ID: {}",
        "Social Security: {}",
        "ID Number: {}",
        "Patient ID (SSN): {}",
        "Government ID: {}",
        "Federal ID: {}"
    ]
    for i in range(num_cases):
        ssn = faker.ssn()
        template = random.choice(ssn_templates)
        ssn_cases.append(template.format(ssn))
    test_cases["US_SSN"] = ssn_cases
    
    # CREDIT_CARD test cases
    cc_cases = []
    cc_templates = [
        "Payment card: {}",
        "Credit card: {}",
        "Card number: {}",
        "Billing card: {}",
        "Insurance card: {}",
        "Payment method: {}",
        "Card on file: {}",
        "Primary card: {}",
        "Backup payment: {}",
        "Emergency card: {}"
    ]
    card_types = ['visa', 'mastercard', 'amex', 'discover']
    for i in range(num_cases):
        card_type = random.choice(card_types)
        try:
            cc_number = faker.credit_card_number(card_type=card_type)
        except:
            cc_number = faker.credit_card_number()
        template = random.choice(cc_templates)
        cc_cases.append(template.format(cc_number))
    test_cases["CREDIT_CARD"] = cc_cases
    
    # ORGANIZATION test cases
    org_cases = []
    org_templates = [
        "Company: {}",
        "Hospital: {}",
        "Insurance: {}",
        "Employer: {}",
        "Provider: {}",
        "Healthcare facility: {}",
        "Medical center: {}",
        "Clinic: {}",
        "Laboratory: {}",
        "Pharmacy: {}",
        "Research facility: {}",
        "Treatment center: {}"
    ]
    org_suffixes = [
        "Medical Center", "Hospital", "Clinic", "Healthcare", "Medical Group",
        "Insurance", "Corp", "Inc", "LLC", "Health System", "Medical Associates",
        "Care Center", "Treatment Center", "Diagnostic Center", "Surgical Center"
    ]
    for i in range(num_cases):
        if random.choice([True, False]):
            org_name = faker.company()
        else:
            org_name = f"{faker.city()} {random.choice(org_suffixes)}"
        template = random.choice(org_templates)
        org_cases.append(template.format(org_name))
    test_cases["ORGANIZATION"] = org_cases
    
    # LOCATION test cases
    location_cases = []
    location_templates = [
        "Treatment at: {}",
        "Patient from: {}",
        "Facility in: {}",
        "Located in: {}",
        "Address: {}",
        "Born in: {}",
        "Transferred from: {}",
        "Referred from: {}",
        "Service area: {}",
        "Coverage area: {}",
        "Branch location: {}",
        "Regional office: {}"
    ]
    location_formats = [
        lambda: f"{faker.city()}, {faker.state()}",
        lambda: f"{faker.city()}, {faker.state_abbr()}",
        lambda: f"{faker.city()}, {faker.country()}",
        lambda: faker.city(),
        lambda: faker.address(),
        lambda: f"{faker.street_address()}, {faker.city()}"
    ]
    for i in range(num_cases):
        location = random.choice(location_formats)()
        template = random.choice(location_templates)
        location_cases.append(template.format(location))
    test_cases["LOCATION"] = location_cases
    
    # DATE_TIME test cases
    datetime_cases = []
    datetime_templates = [
        "Birth Date: {}",
        "Appointment: {}",
        "Admission Date: {}",
        "Discharge: {}",
        "Visit time: {}",
        "Surgery scheduled: {}",
        "Lab date: {}",
        "Follow-up: {}",
        "Last visit: {}",
        "Next appointment: {}"
    ]
    date_formats = [
        lambda: faker.date_of_birth().strftime('%Y-%m-%d'),
        lambda: faker.date_time_this_year().strftime('%Y-%m-%d %H:%M'),
        lambda: faker.date_this_year().strftime('%m/%d/%Y'),
        lambda: faker.date_time_this_month().strftime('%Y-%m-%d %H:%M:%S'),
        lambda: faker.time(),
        lambda: faker.date_between(start_date='-1y', end_date='+1y').strftime('%Y-%m-%d')
    ]
    for i in range(num_cases):
        date_str = random.choice(date_formats)()
        template = random.choice(datetime_templates)
        datetime_cases.append(template.format(date_str))
    test_cases["DATE_TIME"] = datetime_cases
    
    print(f"✅ Generated {sum(len(cases) for cases in test_cases.values())} total test cases")
    return test_cases

async def quick_entity_test(num_cases: int = 100, detection_only: bool = False):
    """Quick test for common entity types with large dataset"""
    
    # Generate large dataset
    test_cases = generate_test_cases(num_cases)

    # Only initialize services that we need
    if detection_only:
        print("🔍 Detection-only mode: Testing PII detection without masking/unmasking")
        masker = None
        unmasker = None
    else:
        masker = PIIMaskerService()
        unmasker = PIIUnmaskerService()
    
    mode_text = "Detection Only" if detection_only else "Full Pipeline"
    print(f"🚀 Quick Entity Test - Large Scale ({num_cases} cases per entity) - {mode_text}")
    print("=" * 80)
    
    # Summary statistics
    total_tests = 0
    total_detected = 0
    total_masked = 0
    total_roundtrip_success = 0
    
    for entity_type, test_texts in test_cases.items():
        print(f"\n🔍 Testing {entity_type} ({len(test_texts)} cases):")
        print("-" * 50)
        
        detected_count = 0
        masked_count = 0
        roundtrip_success_count = 0
        
        # Test a sample of cases to avoid overwhelming output
        sample_size = min(10, len(test_texts))  # Show max 10 examples
        sample_indices = random.sample(range(len(test_texts)), sample_size)
        
        print(f"    📊 Processing all {len(test_texts)} cases (showing {sample_size} examples)...")
        
        for i, text in enumerate(test_texts):
            show_details = i in sample_indices
            
            if show_details:
                print(f"\n    Example {sample_indices.index(i)+1}: {text[:60]}...")
            
            try:
                # Test detection
                detected = await notification_service.detect_pii(text)
                if detected:
                    detected_count += 1
                    total_detected += 1
                
                if show_details and detected:
                    print(f"      🔍 Detected: {len(detected)} entities")
                    for detection in detected[:3]:  # Show max 3 detections
                        print(f"         - {detection['entity_type']}: '{detection['text']}' (score: {detection['score']:.2f})")
                
                # Skip masking/unmasking if detection-only mode
                if detection_only:
                    if show_details:
                        if detected:
                            print(f"      ✅ Detection successful")
                        else:
                            print(f"      ⚠️  No PII detected")
                    total_tests += 1
                    continue
                
                # Test masking  
                masked_text, mapping = await masker.mask_text(text)
                if mapping:
                    masked_count += 1
                    total_masked += 1
                
                if show_details:
                    print(f"      🔒 Masked: {masked_text[:60]}...")
                
                if mapping:
                    if show_details:
                        print(f"      🗝️  Mapping: {len(mapping)} items")
                        for j, (pseudonym, original) in enumerate(list(mapping.items())[:2]):  # Show max 2 mappings
                            print(f"         {pseudonym} → {original}")
                    
                    # Test unmasking
                    unmasked_text = unmasker.unmask_text(masked_text, mapping)
                    
                    # Check roundtrip success
                    if unmasked_text.strip() == text.strip():
                        roundtrip_success_count += 1
                        total_roundtrip_success += 1
                    
                    if show_details:
                        success = "✅" if unmasked_text.strip() == text.strip() else "❌"
                        print(f"      🎯 Roundtrip: {success}")
                else:
                    if show_details:
                        print(f"      ⚠️  No PII detected for masking")
                
                total_tests += 1
                    
            except Exception as e:
                if show_details:
                    print(f"      ❌ Error: {e}")
        
        # Entity summary
        detection_rate = (detected_count / len(test_texts)) * 100
        
        print(f"\n    📈 {entity_type} Summary:")
        print(f"       Detection Rate:  {detection_rate:6.1f}% ({detected_count}/{len(test_texts)})")
        
        if not detection_only:
            masking_rate = (masked_count / len(test_texts)) * 100
            roundtrip_rate = (roundtrip_success_count / len(test_texts)) * 100
            print(f"       Masking Rate:    {masking_rate:6.1f}% ({masked_count}/{len(test_texts)})")
            print(f"       Roundtrip Rate:  {roundtrip_rate:6.1f}% ({roundtrip_success_count}/{len(test_texts)})")

    # Overall summary
    print(f"\n" + "=" * 80)
    print("📊 OVERALL SUMMARY")
    print("=" * 80)
    print(f"📈 Total Test Cases: {total_tests:,}")
    print(f"🔍 Overall Detection Rate: {(total_detected/total_tests)*100:6.1f}% ({total_detected:,}/{total_tests:,})")
    
    if not detection_only:
        print(f"🔒 Overall Masking Rate: {(total_masked/total_tests)*100:6.1f}% ({total_masked:,}/{total_tests:,})")
        print(f"🎯 Overall Roundtrip Rate: {(total_roundtrip_success/total_tests)*100:6.1f}% ({total_roundtrip_success:,}/{total_tests:,})")
    
    test_mode = "detection-only" if detection_only else "full pipeline"
    print(f"\n✅ Large scale {test_mode} test completed!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Quick Entity Test with Large Dataset')
    parser.add_argument('--cases', type=int, default=100, help='Number of test cases per entity (default: 100)')
    parser.add_argument('--small', action='store_true', help='Run small test (10 cases per entity)')
    parser.add_argument('--medium', action='store_true', help='Run medium test (100 cases per entity)')
    parser.add_argument('--large', action='store_true', help='Run large test (500 cases per entity)')
    parser.add_argument('--massive', action='store_true', help='Run massive test (1000 cases per entity)')
    parser.add_argument('--detection-only', action='store_true', help='Only test PII detection (skip masking/unmasking)')
    
    args = parser.parse_args()
    
    if args.small:
        num_cases = 10
    elif args.medium:
        num_cases = 100
    elif args.large:
        num_cases = 500
    elif args.massive:
        num_cases = 1000
    else:
        num_cases = args.cases
    
    mode_text = "detection-only" if args.detection_only else "full pipeline"
    print(f"🚀 Starting Quick Entity Test with {num_cases} cases per entity ({mode_text})...")
    asyncio.run(quick_entity_test(num_cases, args.detection_only))

#!/usr/bin/env python3
"""
Massive Entity Test - Test với số lượng lớn (nghìn test cases) để đo performance
"""

import sys
import os
import asyncio
import random
import time
import json
from typing import Dict, List, Tuple
from faker import Faker
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.services.masking_service import PIIMaskerService
    from app.services.unmasking_service import PIIUnmaskerService
    from app.services.notification_service import notification_service
except ImportError as e:
    print(f"❌ Error importing services: {e}")
    sys.exit(1)

class MassiveEntityTester:
    """
    Test với số lượng massive để đo performance và reliability
    """
    
    def __init__(self, detection_only: bool = False):
        self.faker = Faker(['en_US', 'vi_VN'])
        self.detection_only = detection_only
        
        # Only initialize services we need
        if not detection_only:
            self.masker = PIIMaskerService()
            self.unmasker = PIIUnmaskerService()
        else:
            self.masker = None
            self.unmasker = None
        
    def generate_massive_dataset(self, cases_per_entity: int = 1000) -> Dict[str, List[str]]:
        """Generate massive dataset for performance testing"""
        print(f"🔄 Generating massive dataset: {cases_per_entity:,} cases per entity...")
        start_time = time.time()
        
        test_cases = {}
        
        # PERSON cases - 1000+ variations
        person_cases = []
        person_prefixes = ["Dr.", "Mr.", "Ms.", "Mrs.", "Prof.", "Nurse", "Patient", "Employee", "Staff", "Resident"]
        person_contexts = [
            "{} {} was admitted to the hospital",
            "Contact person: {} {}",
            "Patient name: {} {}",
            "Physician {} {} treated the patient",
            "Employee {} {} works in cardiology",
            "Specialist {} {} performed surgery",
            "Consultant {} {} reviewed the case", 
            "Therapist {} {} provided treatment",
            "Technician {} {} ran the tests",
            "Administrator {} {} handles billing"
        ]
        
        for i in range(cases_per_entity):
            name = self.faker.name()
            if random.choice([True, False, False]):  # 1/3 chance for prefix
                prefix = random.choice(person_prefixes)
                context = random.choice(person_contexts).format(prefix, name)
            else:
                context = random.choice(person_contexts).format("", name).replace("  ", " ")
            person_cases.append(context)
        test_cases["PERSON"] = person_cases
        
        # EMAIL cases - 1000+ variations
        email_cases = []
        email_domains = ["gmail.com", "yahoo.com", "outlook.com", "hospital.org", "clinic.com", "medical.edu", "health.gov"]
        email_contexts = [
            "Primary email: {}",
            "Send lab results to: {}",
            "Patient contact: {}",
            "Emergency contact email: {}",
            "Insurance correspondence: {}",
            "Billing inquiries: {}",
            "Appointment confirmations: {}",
            "Medical records request: {}",
            "Provider communication: {}",
            "Pharmacy notifications: {}"
        ]
        
        for i in range(cases_per_entity):
            if random.choice([True, False]):
                email = self.faker.email()
            else:
                username = self.faker.user_name()
                domain = random.choice(email_domains)
                email = f"{username}@{domain}"
            context = random.choice(email_contexts).format(email)
            email_cases.append(context)
        test_cases["EMAIL_ADDRESS"] = email_cases
        
        # PHONE cases - 1000+ variations
        phone_cases = []
        phone_formats = [
            "+1-{}-{}-{}",
            "({}) {}-{}",
            "{}.{}.{}",
            "{}-{}-{}",
            "+1 {} {} {}",
            "1-{}-{}-{}",
            "({}) {} {}"
        ]
        phone_contexts = [
            "Primary phone: {}",
            "Emergency contact: {}",
            "Hospital main line: {}",
            "Direct line: {}",
            "Mobile number: {}",
            "Office phone: {}",
            "After hours: {}",
            "Appointment line: {}",
            "Insurance hotline: {}",
            "Pharmacy phone: {}"
        ]
        
        for i in range(cases_per_entity):
            area = self.faker.random_int(100, 999)
            exchange = self.faker.random_int(100, 999)
            number = self.faker.random_int(1000, 9999)
            format_str = random.choice(phone_formats)
            if format_str.count("{}") == 3:
                phone = format_str.format(area, exchange, number)
            else:
                phone = format_str.format(f"{area}{exchange}{number}")
            context = random.choice(phone_contexts).format(phone)
            phone_cases.append(context)
        test_cases["PHONE_NUMBER"] = phone_cases
        
        # SSN cases - 1000+ variations
        ssn_cases = []
        ssn_contexts = [
            "Patient SSN: {}",
            "Social Security Number: {}",
            "Tax ID: {}",
            "Government ID: {}",
            "Medicare ID: {}",
            "Employee SSN: {}",
            "Primary identifier: {}",
            "Federal ID: {}",
            "Social Security: {}",
            "Identity verification: {}"
        ]
        
        for i in range(cases_per_entity):
            ssn = self.faker.ssn()
            context = random.choice(ssn_contexts).format(ssn)
            ssn_cases.append(context)
        test_cases["US_SSN"] = ssn_cases
        
        # CREDIT_CARD cases
        cc_cases = []
        cc_types = ['visa', 'mastercard', 'amex', 'discover']
        cc_contexts = [
            "Payment method: {}",
            "Credit card: {}",
            "Insurance card: {}",
            "Billing card: {}",
            "Primary payment: {}",
            "Backup card: {}",
            "Emergency payment: {}",
            "Auto-pay card: {}",
            "Copay card: {}",
            "HSA card: {}"
        ]
        
        for i in range(cases_per_entity):
            try:
                cc_type = random.choice(cc_types)
                cc_number = self.faker.credit_card_number(card_type=cc_type)
            except:
                cc_number = self.faker.credit_card_number()
            context = random.choice(cc_contexts).format(cc_number)
            cc_cases.append(context)
        test_cases["CREDIT_CARD"] = cc_cases
        
        # Generate other entity types...
        # (Similar pattern for ORGANIZATION, LOCATION, etc.)
        
        generation_time = time.time() - start_time
        total_cases = sum(len(cases) for cases in test_cases.values())
        print(f"✅ Generated {total_cases:,} test cases in {generation_time:.1f} seconds")
        print(f"   Average: {total_cases/generation_time:.0f} cases/second")
        
        return test_cases
    
    async def run_massive_test(self, cases_per_entity: int = 1000, batch_size: int = 100):
        """Run massive scale test with batching for performance"""
        mode_text = "Detection Only" if self.detection_only else "Full Pipeline"
        print(f"🚀 Massive Entity Test - {cases_per_entity:,} cases per entity - {mode_text}")
        print("=" * 80)
        
        # Generate dataset
        test_cases = self.generate_massive_dataset(cases_per_entity)
        
        results = {
            "test_config": {
                "cases_per_entity": cases_per_entity,
                "batch_size": batch_size,
                "timestamp": datetime.now().isoformat(),
                "total_cases": sum(len(cases) for cases in test_cases.values()),
                "detection_only": self.detection_only
            },
            "entity_results": {},
            "overall_stats": {}
        }
        
        total_start_time = time.time()
        
        for entity_type, test_texts in test_cases.items():
            print(f"\n🔍 Testing {entity_type} ({len(test_texts):,} cases):")
            print("-" * 60)
            
            entity_start_time = time.time()
            detected_count = 0
            masked_count = 0
            roundtrip_success_count = 0
            error_count = 0
            
            # Process in batches for better performance
            for batch_start in range(0, len(test_texts), batch_size):
                batch_end = min(batch_start + batch_size, len(test_texts))
                batch = test_texts[batch_start:batch_end]
                
                print(f"    Processing batch {batch_start//batch_size + 1}/{(len(test_texts)-1)//batch_size + 1} "
                      f"({batch_start+1:,}-{batch_end:,})")
                
                batch_results = await self.process_batch(batch)
                
                detected_count += batch_results["detected"]
                masked_count += batch_results["masked"]
                roundtrip_success_count += batch_results["roundtrip_success"]
                error_count += batch_results["errors"]
            
            entity_time = time.time() - entity_start_time
            
            # Calculate rates
            detection_rate = (detected_count / len(test_texts)) * 100
            error_rate = (error_count / len(test_texts)) * 100
            throughput = len(test_texts) / entity_time
            
            # Store results - conditional based on detection_only mode
            entity_result = {
                "total_cases": len(test_texts),
                "detected": detected_count,
                "detection_rate": detection_rate,
                "error_rate": error_rate,
                "processing_time": entity_time,
                "throughput": throughput,
                "errors": error_count
            }
            
            if not self.detection_only:
                masking_rate = (masked_count / len(test_texts)) * 100
                roundtrip_rate = (roundtrip_success_count / len(test_texts)) * 100
                entity_result.update({
                    "masked": masked_count,
                    "roundtrip_success": roundtrip_success_count,
                    "masking_rate": masking_rate,
                    "roundtrip_rate": roundtrip_rate
                })
            
            results["entity_results"][entity_type] = entity_result
            
            # Print summary
            print(f"\n    📈 {entity_type} Results:")
            print(f"       Detection Rate:  {detection_rate:6.1f}% ({detected_count:,}/{len(test_texts):,})")
            if not self.detection_only:
                print(f"       Masking Rate:    {masking_rate:6.1f}% ({masked_count:,}/{len(test_texts):,})")
                print(f"       Roundtrip Rate:  {roundtrip_rate:6.1f}% ({roundtrip_success_count:,}/{len(test_texts):,})")
            print(f"       Error Rate:      {error_rate:6.1f}% ({error_count:,}/{len(test_texts):,})")
            print(f"       Processing Time: {entity_time:6.1f}s")
            print(f"       Throughput:      {throughput:6.1f} cases/second")
        
        total_time = time.time() - total_start_time
        total_cases = sum(len(cases) for cases in test_cases.values())
        overall_throughput = total_cases / total_time
        
        # Overall statistics
        total_detected = sum(r["detected"] for r in results["entity_results"].values())
        total_errors = sum(r["errors"] for r in results["entity_results"].values())
        
        overall_stats = {
            "total_cases": total_cases,
            "total_detected": total_detected,
            "total_errors": total_errors,
            "overall_detection_rate": (total_detected / total_cases) * 100,
            "overall_error_rate": (total_errors / total_cases) * 100,
            "total_processing_time": total_time,
            "overall_throughput": overall_throughput
        }
        
        if not self.detection_only:
            total_masked = sum(r.get("masked", 0) for r in results["entity_results"].values())
            total_roundtrip = sum(r.get("roundtrip_success", 0) for r in results["entity_results"].values())
            overall_stats.update({
                "total_masked": total_masked,
                "total_roundtrip_success": total_roundtrip,
                "overall_masking_rate": (total_masked / total_cases) * 100,
                "overall_roundtrip_rate": (total_roundtrip / total_cases) * 100
            })
        
        results["overall_stats"] = overall_stats
        
        # Print overall summary
        self.print_overall_summary(results)
        
        # Save results
        self.save_results(results, cases_per_entity)
        
        return results
    
    async def process_batch(self, batch: List[str]) -> Dict[str, int]:
        """Process a batch of test cases"""
        detected = 0
        masked = 0
        roundtrip_success = 0
        errors = 0
        
        for text in batch:
            try:
                # Test detection
                detected_entities = await notification_service.detect_pii(text)
                if detected_entities:
                    detected += 1
                
                # Skip masking if detection-only mode
                if self.detection_only:
                    continue
                
                # Test masking
                masked_text, mapping = await self.masker.mask_text(text)
                if mapping:
                    masked += 1
                    
                    # Test unmasking
                    unmasked_text = self.unmasker.unmask_text(masked_text, mapping)
                    if unmasked_text.strip() == text.strip():
                        roundtrip_success += 1
                        
            except Exception as e:
                errors += 1
        
        return {
            "detected": detected,
            "masked": masked,
            "roundtrip_success": roundtrip_success,
            "errors": errors
        }
    
    def print_overall_summary(self, results: Dict):
        """Print comprehensive summary"""
        stats = results["overall_stats"]
        
        print(f"\n" + "=" * 80)
        print("📊 MASSIVE TEST SUMMARY")
        print("=" * 80)
        print(f"📈 Total Test Cases:     {stats['total_cases']:,}")
        print(f"🔍 Overall Detection:    {stats['overall_detection_rate']:6.1f}% ({stats['total_detected']:,})")
        
        if not self.detection_only:
            print(f"🔒 Overall Masking:      {stats['overall_masking_rate']:6.1f}% ({stats['total_masked']:,})")
            print(f"🎯 Overall Roundtrip:    {stats['overall_roundtrip_rate']:6.1f}% ({stats['total_roundtrip_success']:,})")
        
        print(f"❌ Overall Errors:       {stats['overall_error_rate']:6.1f}% ({stats['total_errors']:,})")
        print(f"⏱️  Total Time:          {stats['total_processing_time']:6.1f} seconds")
        print(f"🚀 Overall Throughput:   {stats['overall_throughput']:6.1f} cases/second")
        
        print(f"\n📋 Performance by Entity:")
        if self.detection_only:
            print(f"{'Entity':<15} {'Cases':<8} {'Detection':<10} {'Errors':<7} {'Speed':<10}")
            print("-" * 60)
        else:
            print(f"{'Entity':<15} {'Cases':<8} {'Detection':<10} {'Masking':<9} {'Roundtrip':<10} {'Errors':<7} {'Speed':<10}")
            print("-" * 80)
        
        for entity, result in results["entity_results"].items():
            if self.detection_only:
                print(f"{entity:<15} {result['total_cases']:<8,} {result['detection_rate']:<9.1f}% "
                      f"{result['error_rate']:<6.1f}% {result['throughput']:<9.1f}/s")
            else:
                print(f"{entity:<15} {result['total_cases']:<8,} {result['detection_rate']:<9.1f}% "
                      f"{result['masking_rate']:<8.1f}% {result['roundtrip_rate']:<9.1f}% "
                      f"{result['error_rate']:<6.1f}% {result['throughput']:<9.1f}/s")
    
    def save_results(self, results: Dict, cases_per_entity: int):
        """Save detailed results to JSON"""
        mode_suffix = "_detection_only" if self.detection_only else "_full"
        filename = f"massive_entity_test_{cases_per_entity}_cases{mode_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed results saved to: {filename}")


async def main():
    """Main function with argument parsing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Massive Entity Testing for Performance Analysis')
    parser.add_argument('--cases', type=int, default=1000, help='Cases per entity (default: 1000)')
    parser.add_argument('--batch', type=int, default=100, help='Batch size for processing (default: 100)')
    parser.add_argument('--small', action='store_true', help='Small test: 100 cases per entity')
    parser.add_argument('--medium', action='store_true', help='Medium test: 1000 cases per entity')
    parser.add_argument('--large', action='store_true', help='Large test: 5000 cases per entity')
    parser.add_argument('--massive', action='store_true', help='Massive test: 10000 cases per entity')
    parser.add_argument('--detection-only', action='store_true', help='Only test PII detection (skip masking/unmasking)')
    
    args = parser.parse_args()
    
    # Determine number of cases
    if args.small:
        cases = 100
    elif args.medium:
        cases = 1000
    elif args.large:
        cases = 5000
    elif args.massive:
        cases = 10000
    else:
        cases = args.cases
    
    tester = MassiveEntityTester(detection_only=args.detection_only)
    
    mode_text = "detection-only" if args.detection_only else "full pipeline"
    print(f"🚀 Starting Massive Entity Test: {cases:,} cases per entity ({mode_text})")
    
    await tester.run_massive_test(cases, args.batch)


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Comprehensive Entity Test - Kiểm tra chi tiết từng loại entity trong pseudonym_map
Tạo dữ liệu test chuyên biệt cho từng loại PII và đo lường hiệu suất cụ thể
"""

import sys
import os
import json
import asyncio
from typing import Dict, List, Tuple
from datetime import datetime
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

class ComprehensiveEntityTester:
    """
    Test chuyên sâu cho từng loại entity trong pseudonym_map
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
        
        # Entity test data generators tương ứng với pseudonym_map
        self.entity_generators = {
            "PERSON": self._generate_person_data,
            "EMAIL_ADDRESS": self._generate_email_data,
            "PHONE_NUMBER": self._generate_phone_data,
            "US_SSN": self._generate_ssn_data,
            "DATE_TIME": self._generate_datetime_data,
            "CREDIT_CARD": self._generate_credit_card_data,
            "ADDRESS": self._generate_address_data,
            "LOCATION": self._generate_location_data,
            "ORG": self._generate_organization_data,
            "ORGANIZATION": self._generate_organization_data,
            "AGE": self._generate_age_data,
            "ID": self._generate_id_data,
            # Medical/Healthcare entities
            "PATIENT": self._generate_patient_data,
            "STAFF": self._generate_staff_data,
            "HOSPITAL": self._generate_hospital_data,
            "FACILITY": self._generate_facility_data,
            "VENDOR": self._generate_vendor_data,
        }
        
        # Expected pseudonym patterns
        self.expected_patterns = {
            "PERSON": "Name_",
            "EMAIL_ADDRESS": "Email_",
            "PHONE_NUMBER": "Phone_",
            "US_SSN": "US_SSN_",
            "DATE_TIME": "Date_",
            "CREDIT_CARD": "CC_",
            "ADDRESS": "Address_",
            "LOCATION": "LOCATION_",
            "ORG": "ORGANIZATION_",
            "ORGANIZATION": "ORGANIZATION_",
            "AGE": "AGE_",
            "ID": "ID_",
            "PATIENT": "PERSON_",
            "STAFF": "PERSON_",
            "HOSPITAL": "ORGANIZATION_",
            "FACILITY": "LOCATION_",
            "VENDOR": "ORGANIZATION_"
        }

    def _generate_person_data(self, count: int = 10) -> List[str]:
        """Generate person names"""
        return [
            f"Customer: {self.faker.name()}",
            f"Patient Name: {self.faker.name()}",
            f"Dr. {self.faker.name()}",
            f"Contact person: {self.faker.first_name()} {self.faker.last_name()}",
            f"Employee: {self.faker.name()}"
        ][:count]

    def _generate_email_data(self, count: int = 10) -> List[str]:
        """Generate email addresses"""
        return [
            f"Email: {self.faker.email()}",
            f"Contact email: {self.faker.company_email()}",
            f"Send to: {self.faker.email()}",
            f"Patient email: {self.faker.free_email()}",
            f"Staff email: {self.faker.email()}"
        ][:count]

    def _generate_phone_data(self, count: int = 10) -> List[str]:
        """Generate phone numbers"""
        return [
            f"Phone: {self.faker.phone_number()}",
            f"Contact: +1-555-{self.faker.random_int(100, 999)}-{self.faker.random_int(1000, 9999)}",
            f"Mobile: (555) {self.faker.random_int(100, 999)}-{self.faker.random_int(1000, 9999)}",
            f"Emergency contact: {self.faker.phone_number()}",
            f"Office: +1 555 {self.faker.random_int(100, 999)} {self.faker.random_int(1000, 9999)}"
        ][:count]

    def _generate_ssn_data(self, count: int = 10) -> List[str]:
        """Generate SSN numbers"""
        return [
            f"SSN: {self.faker.ssn()}",
            f"Social Security: {self.faker.ssn()}",
            f"Patient SSN: {self.faker.ssn()}",
            f"Employee SSN: {self.faker.ssn()}",
            f"Tax ID: {self.faker.ssn()}"
        ][:count]

    def _generate_datetime_data(self, count: int = 10) -> List[str]:
        """Generate date/time data"""
        return [
            f"Birth Date: {self.faker.date_of_birth().strftime('%Y-%m-%d')}",
            f"Appointment: {self.faker.date_time_this_year().strftime('%Y-%m-%d %H:%M')}",
            f"Admission Date: {self.faker.date_this_year().strftime('%m/%d/%Y')}",
            f"Discharge: {self.faker.date_time_this_month().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Visit time: {self.faker.time()}"
        ][:count]

    def _generate_credit_card_data(self, count: int = 10) -> List[str]:
        """Generate credit card numbers"""
        return [
            f"Card: {self.faker.credit_card_number()}",
            f"Payment method: {self.faker.credit_card_number(card_type='visa')}",
            f"Credit card: {self.faker.credit_card_number(card_type='mastercard')}",
            f"Billing card: {self.faker.credit_card_number(card_type='amex')}",
            f"Insurance card: {self.faker.credit_card_number()}"
        ][:count]

    def _generate_address_data(self, count: int = 10) -> List[str]:
        """Generate addresses"""
        return [
            f"Address: {self.faker.address()}",
            f"Home: {self.faker.street_address()}, {self.faker.city()}, {self.faker.state()} {self.faker.zipcode()}",
            f"Office location: {self.faker.address()}",
            f"Shipping to: {self.faker.address()}",
            f"Patient address: {self.faker.address()}"
        ][:count]

    def _generate_location_data(self, count: int = 10) -> List[str]:
        """Generate location data"""
        return [
            f"Location: {self.faker.city()}, {self.faker.state()}",
            f"Born in: {self.faker.city()}",
            f"Treatment at: {self.faker.city()} Medical Center",
            f"Facility in: {self.faker.city()}, {self.faker.country()}",
            f"Branch: {self.faker.city()} Office"
        ][:count]

    def _generate_organization_data(self, count: int = 10) -> List[str]:
        """Generate organization data"""
        return [
            f"Company: {self.faker.company()}",
            f"Employer: {self.faker.company()} Corp",
            f"Insurance: {self.faker.company()} Insurance",
            f"Organization: {self.faker.company()} Healthcare",
            f"Provider: {self.faker.company()} Medical Group"
        ][:count]

    def _generate_age_data(self, count: int = 10) -> List[str]:
        """Generate age data"""
        return [
            f"Age: {self.faker.random_int(18, 80)} years old",
            f"Patient age: {self.faker.random_int(1, 100)}",
            f"Born {self.faker.random_int(20, 70)} years ago",
            f"Age at admission: {self.faker.random_int(18, 90)}",
            f"{self.faker.random_int(25, 65)} year old patient"
        ][:count]

    def _generate_id_data(self, count: int = 10) -> List[str]:
        """Generate ID numbers"""
        return [
            f"Patient ID: {self.faker.random_int(100000, 999999)}",
            f"Medical Record: MR-{self.faker.random_int(10000, 99999)}",
            f"Employee ID: EMP{self.faker.random_int(1000, 9999)}",
            f"Account Number: {self.faker.random_int(1000000, 9999999)}",
            f"Reference ID: REF-{self.faker.random_int(10000, 99999)}"
        ][:count]

    def _generate_patient_data(self, count: int = 10) -> List[str]:
        """Generate patient-specific data"""
        return [
            f"Patient: {self.faker.name()}",
            f"Patient Name: {self.faker.name()}",
            f"Pt: {self.faker.name()}",
            f"Patient {self.faker.name()} was admitted",
            f"The patient {self.faker.name()} requires"
        ][:count]

    def _generate_staff_data(self, count: int = 10) -> List[str]:
        """Generate staff/healthcare worker data"""
        return [
            f"Dr. {self.faker.name()}",
            f"Nurse {self.faker.name()}",
            f"Staff member: {self.faker.name()}",
            f"Healthcare worker: {self.faker.name()}",
            f"Physician: Dr. {self.faker.last_name()}"
        ][:count]

    def _generate_hospital_data(self, count: int = 10) -> List[str]:
        """Generate hospital/healthcare organization data"""
        return [
            f"Hospital: {self.faker.city()} General Hospital",
            f"Medical Center: {self.faker.company()} Medical Center",
            f"Clinic: {self.faker.city()} Family Clinic",
            f"Healthcare facility: {self.faker.company()} Healthcare",
            f"Hospital network: {self.faker.company()} Health System"
        ][:count]

    def _generate_facility_data(self, count: int = 10) -> List[str]:
        """Generate healthcare facility data"""
        return [
            f"Facility: {self.faker.city()} Medical Facility",
            f"Treatment center: {self.faker.company()} Treatment Center",
            f"Care facility: {self.faker.city()} Care Center",
            f"Medical facility in {self.faker.city()}",
            f"Healthcare facility: {self.faker.company()} Center"
        ][:count]

    def _generate_vendor_data(self, count: int = 10) -> List[str]:
        """Generate vendor/supplier data"""
        return [
            f"Vendor: {self.faker.company()} Medical Supplies",
            f"Supplier: {self.faker.company()} Corp",
            f"Medical vendor: {self.faker.company()} Healthcare",
            f"Equipment vendor: {self.faker.company()} Medical",
            f"Service provider: {self.faker.company()} Services"
        ][:count]

    async def test_entity_type(self, entity_type: str, sample_count: int = 5) -> Dict:
        """Test specific entity type"""
        print(f"🔍 Testing {entity_type}...")
        
        if entity_type not in self.entity_generators:
            print(f"⚠️  No generator for {entity_type}")
            return {"entity_type": entity_type, "status": "no_generator"}

        # Generate test data
        test_data = self.entity_generators[entity_type](sample_count)
        
        results = {
            "entity_type": entity_type,
            "expected_pattern": self.expected_patterns.get(entity_type, "UNKNOWN_"),
            "test_cases": [],
            "success_count": 0,
            "total_count": len(test_data),
            "detection_rate": 0.0,
            "masking_rate": 0.0,
            "pattern_match_rate": 0.0
        }

        for i, test_text in enumerate(test_data):
            print(f"  Testing case {i+1}/{len(test_data)}: {test_text[:50]}...")
            
            case_result = {
                "original_text": test_text,
                "detected": False,
                "masked_successfully": False,
                "pattern_matches": False,
                "masked_text": "",
                "mapping": {},
                "error": None
            }

            try:
                # Test detection
                detected = await notification_service.detect_pii(test_text)
                case_result["detected"] = len(detected) > 0

                # Skip masking if detection-only mode
                if self.detection_only:
                    if case_result["detected"]:
                        results["success_count"] += 1
                else:
                    # Test masking
                    masked_text, mapping = await self.masker.mask_text(test_text)
                    case_result["masked_text"] = masked_text
                    case_result["mapping"] = mapping
                    case_result["masked_successfully"] = masked_text != test_text

                    # Check pseudonym pattern
                    expected_pattern = self.expected_patterns.get(entity_type, "")
                    if mapping:
                        for pseudonym in mapping.keys():
                            if expected_pattern in pseudonym:
                                case_result["pattern_matches"] = True
                                break

                    if case_result["detected"] and case_result["masked_successfully"]:
                        results["success_count"] += 1

            except Exception as e:
                case_result["error"] = str(e)
                print(f"    ❌ Error: {e}")

            results["test_cases"].append(case_result)

        # Calculate rates
        results["detection_rate"] = sum(1 for case in results["test_cases"] if case["detected"]) / len(test_data)
        
        if not self.detection_only:
            results["masking_rate"] = sum(1 for case in results["test_cases"] if case["masked_successfully"]) / len(test_data)
            results["pattern_match_rate"] = sum(1 for case in results["test_cases"] if case["pattern_matches"]) / len(test_data)
        else:
            results["masking_rate"] = 0.0
            results["pattern_match_rate"] = 0.0

        return results

    async def run_comprehensive_test(self, entities_to_test: List[str] = None, sample_count: int = 5):
        """Run comprehensive test for all or specified entities"""
        if entities_to_test is None:
            entities_to_test = list(self.entity_generators.keys())

        mode_text = "Detection Only" if self.detection_only else "Full Pipeline"
        print(f"🚀 Comprehensive Entity Testing - {mode_text}")
        print("=" * 50)
        print(f"Testing {len(entities_to_test)} entity types with {sample_count} samples each")
        print()

        all_results = []
        
        for entity_type in entities_to_test:
            result = await self.test_entity_type(entity_type, sample_count)
            all_results.append(result)
            
            # Print summary for this entity
            print(f"✅ {entity_type}:")
            print(f"   Detection Rate: {result['detection_rate']:.1%}")
            if not self.detection_only:
                print(f"   Masking Rate: {result['masking_rate']:.1%}")
                print(f"   Pattern Match Rate: {result['pattern_match_rate']:.1%}")
            print()

        # Overall summary
        self._print_overall_summary(all_results)
        
        # Save detailed results
        self._save_results(all_results)

        return all_results

    def _print_overall_summary(self, results: List[Dict]):
        """Print overall test summary"""
        print("📊 OVERALL SUMMARY")
        print("=" * 50)
        
        total_cases = sum(r["total_count"] for r in results)
        total_detected = sum(len([c for c in r["test_cases"] if c["detected"]]) for r in results)
        total_masked = sum(len([c for c in r["test_cases"] if c["masked_successfully"]]) for r in results)
        total_pattern_match = sum(len([c for c in r["test_cases"] if c["pattern_matches"]]) for r in results)

        print(f"📈 Total Test Cases: {total_cases}")
        print(f"🔍 Overall Detection Rate: {total_detected/total_cases:.1%}")
        print(f"🔒 Overall Masking Rate: {total_masked/total_cases:.1%}")
        print(f"🎯 Overall Pattern Match Rate: {total_pattern_match/total_cases:.1%}")
        print()

        # Entity-specific performance
        print("📋 Entity Performance Breakdown:")
        for result in sorted(results, key=lambda x: x["detection_rate"], reverse=True):
            print(f"   {result['entity_type']:15} | Det: {result['detection_rate']:>5.1%} | Mask: {result['masking_rate']:>5.1%} | Pattern: {result['pattern_match_rate']:>5.1%}")

    def _save_results(self, results: List[Dict]):
        """Save detailed results to JSON file"""
        mode_suffix = "_detection_only" if self.detection_only else "_full"
        filename = f"comprehensive_entity_test_results{mode_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        if self.detection_only:
            output = {
                "timestamp": datetime.now().isoformat(),
                "test_mode": "detection_only",
                "test_summary": {
                    "total_entities_tested": len(results),
                    "total_test_cases": sum(r["total_count"] for r in results),
                    "overall_detection_rate": sum(len([c for c in r["test_cases"] if c["detected"]]) for r in results) / sum(r["total_count"] for r in results)
                },
                "detailed_results": results
            }
        else:
            output = {
                "timestamp": datetime.now().isoformat(),
                "test_mode": "full_pipeline",
                "test_summary": {
                    "total_entities_tested": len(results),
                    "total_test_cases": sum(r["total_count"] for r in results),
                    "overall_detection_rate": sum(len([c for c in r["test_cases"] if c["detected"]]) for r in results) / sum(r["total_count"] for r in results),
                    "overall_masking_rate": sum(len([c for c in r["test_cases"] if c["masked_successfully"]]) for r in results) / sum(r["total_count"] for r in results),
                    "overall_pattern_match_rate": sum(len([c for c in r["test_cases"] if c["pattern_matches"]]) for r in results) / sum(r["total_count"] for r in results)
                },
                "detailed_results": results
            }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Detailed results saved to: {filename}")


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive Entity Testing')
    parser.add_argument('--entities', nargs='+', help='Specific entities to test')
    parser.add_argument('--samples', type=int, default=5, help='Number of samples per entity (default: 5)')
    parser.add_argument('--list', action='store_true', help='List available entities')
    parser.add_argument('--detection-only', action='store_true', help='Only test PII detection (skip masking/unmasking)')
    
    args = parser.parse_args()
    
    tester = ComprehensiveEntityTester(detection_only=args.detection_only)
    
    if args.list:
        print("Available entities to test:")
        for entity in sorted(tester.entity_generators.keys()):
            pattern = tester.expected_patterns.get(entity, "UNKNOWN_")
            print(f"  {entity:15} → {pattern}")
        return
    
    entities_to_test = args.entities if args.entities else None
    await tester.run_comprehensive_test(entities_to_test, args.samples)


if __name__ == "__main__":
    asyncio.run(main())

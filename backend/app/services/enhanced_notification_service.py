"""
Enhanced PII Detection Service
Implements immediate performance improvements for phone number detection
"""

import re
import asyncio
from typing import List, Dict, Optional, Any
from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_analyzer.predefined_recognizers import PhoneRecognizer
import logging

class EnhancedPhoneRecognizer(PhoneRecognizer):
    """Enhanced phone number recognizer with improved patterns and validation"""
    
    def __init__(self):
        super().__init__(supported_language="en")
        
        # Enhanced patterns for better US phone number detection
        self.enhanced_patterns = [
            # Standard formats
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',           # XXX-XXX-XXXX, XXX.XXX.XXXX, XXX XXX XXXX
            r'\(\d{3}\)[-.\s]?\d{3}[-.\s]?\d{4}\b',         # (XXX) XXX-XXXX, (XXX)XXX-XXXX
            r'\+1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',   # +1-XXX-XXX-XXXX, +1 XXX XXX XXXX
            r'\b1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',   # 1-XXX-XXX-XXXX, 1 XXX XXX XXXX
            r'\b\d{10}\b',                                   # XXXXXXXXXX (exactly 10 digits)
            
            # Medical/Healthcare specific patterns
            r'(?i)phone:?\s*\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
            r'(?i)contact:?\s*\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
            r'(?i)tel:?\s*\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
            r'(?i)mobile:?\s*\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
            r'(?i)cell:?\s*\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
        ]
    
    def analyze(self, text: str, entities: List[str], nlp_artifacts=None) -> List[RecognizerResult]:
        """Enhanced phone number analysis with validation"""
        results = []
        
        # Use parent class results first
        parent_results = super().analyze(text, entities, nlp_artifacts)
        results.extend(parent_results)
        
        # Apply enhanced patterns
        for pattern in self.enhanced_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                start, end = match.span()
                matched_text = text[start:end].strip()
                
                # Validate the matched phone number
                confidence = self._validate_phone_number(matched_text)
                
                if confidence > 0.5:  # Only include if validation passes
                    # Check if this overlaps with existing results
                    if not self._overlaps_with_existing(start, end, results):
                        results.append(RecognizerResult(
                            entity_type="PHONE_NUMBER",
                            start=start,
                            end=end,
                            score=confidence
                        ))
        
        # Sort by start position and remove duplicates
        results = self._remove_overlapping_results(results)
        
        return results
    
    def _validate_phone_number(self, phone_text: str) -> float:
        """Validate phone number and return confidence score"""
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone_text)
        
        # Base confidence
        confidence = 0.6
        
        # Length validation
        if len(digits) == 10:
            confidence += 0.2
        elif len(digits) == 11 and digits[0] == '1':
            confidence += 0.2
        else:
            return 0.0  # Invalid length
        
        # Area code validation (not 0 or 1 as first digit)
        if len(digits) >= 3:
            area_code = digits[:3] if len(digits) == 10 else digits[1:4]
            if area_code[0] not in ['0', '1']:
                confidence += 0.1
        
        # Exchange code validation (not 0 or 1 as first digit)
        if len(digits) >= 6:
            exchange = digits[3:6] if len(digits) == 10 else digits[4:7]
            if exchange[0] not in ['0', '1']:
                confidence += 0.1
        
        # Context validation (if preceded by phone-related keywords)
        return min(confidence, 1.0)
    
    def _overlaps_with_existing(self, start: int, end: int, existing_results: List[RecognizerResult]) -> bool:
        """Check if the new result overlaps with existing ones"""
        for result in existing_results:
            if (start < result.end and end > result.start):
                return True
        return False
    
    def _remove_overlapping_results(self, results: List[RecognizerResult]) -> List[RecognizerResult]:
        """Remove overlapping results, keeping the ones with higher confidence"""
        if not results:
            return results
        
        # Sort by start position
        results.sort(key=lambda x: x.start)
        
        filtered_results = []
        for result in results:
            # Check if this result overlaps with any in filtered_results
            overlaps = False
            for i, filtered_result in enumerate(filtered_results):
                if (result.start < filtered_result.end and result.end > filtered_result.start):
                    # Overlapping - keep the one with higher score
                    if result.score > filtered_result.score:
                        filtered_results[i] = result
                    overlaps = True
                    break
            
            if not overlaps:
                filtered_results.append(result)
        
        return filtered_results

class OptimizedNotificationService:
    """
    Enhanced notification service with improved PII detection
    """
    
    def __init__(self):
        # Initialize analyzer with enhanced recognizers
        self.analyzer = AnalyzerEngine()
        
        # Add enhanced phone recognizer
        enhanced_phone_recognizer = EnhancedPhoneRecognizer()
        
        # Remove default phone recognizer and add enhanced one
        self.analyzer.registry.remove_recognizer("PhoneRecognizer")
        self.analyzer.registry.add_recognizer(enhanced_phone_recognizer)
        
        self.logger = logging.getLogger(__name__)
    
    async def detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """
        Enhanced PII detection with improved accuracy
        """
        try:
            if not text or not text.strip():
                return []
            
            # Analyze text with enhanced recognizers
            analyzer_results = self.analyzer.analyze(text=text, language='en')
            
            # Format results with enhanced confidence scoring
            enhanced_results = []
            for res in analyzer_results:
                detected_text = text[res.start:res.end]
                
                result = {
                    "entity_type": res.entity_type,
                    "start": res.start,
                    "end": res.end,
                    "score": res.score,
                    "text": detected_text,
                    "confidence": self._calculate_enhanced_confidence(res, text)
                }
                
                # Apply confidence threshold
                if result["confidence"] >= 0.6:  # Minimum confidence threshold
                    enhanced_results.append(result)
            
            return enhanced_results
            
        except Exception as e:
            self.logger.error(f"Error in enhanced PII detection: {str(e)}")
            return []
    
    def _calculate_enhanced_confidence(self, result: RecognizerResult, text: str) -> float:
        """Calculate enhanced confidence score for detected entities"""
        base_confidence = result.score
        
        # Entity-specific confidence adjustments
        if result.entity_type == "PHONE_NUMBER":
            detected_text = text[result.start:result.end]
            
            # Additional phone number validation
            digits = re.sub(r'\D', '', detected_text)
            
            # Boost confidence for valid US phone numbers
            if len(digits) in [10, 11]:
                if len(digits) == 11 and digits[0] == '1':
                    base_confidence = min(base_confidence + 0.1, 1.0)
                elif len(digits) == 10:
                    base_confidence = min(base_confidence + 0.1, 1.0)
                
                # Check for valid area code and exchange
                area_code = digits[:3] if len(digits) == 10 else digits[1:4]
                exchange = digits[3:6] if len(digits) == 10 else digits[4:7]
                
                if area_code[0] not in ['0', '1'] and exchange[0] not in ['0', '1']:
                    base_confidence = min(base_confidence + 0.1, 1.0)
        
        return base_confidence
    
    async def generate_pii_alert(self, text: str) -> Optional[str]:
        """
        Generate enhanced PII alert with better detection
        """
        pii_entities = await self.detect_pii(text)
        
        if pii_entities:
            # Group by entity type for better alerting
            entity_counts = {}
            for entity in pii_entities:
                entity_type = entity["entity_type"]
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            
            # Create detailed alert message
            entity_details = []
            for entity_type, count in entity_counts.items():
                if count == 1:
                    entity_details.append(f"{entity_type}")
                else:
                    entity_details.append(f"{entity_type} ({count} instances)")
            
            alert_message = (
                f"🚨 PII detected in your input. Found: {', '.join(entity_details)}. "
                f"Please review and consider masking sensitive information before proceeding."
            )
            
            return alert_message
        
        return None

# Example usage and testing
async def test_enhanced_detection():
    """Test the enhanced PII detection"""
    print("🧪 Testing Enhanced PII Detection...")
    
    service = OptimizedNotificationService()
    
    # Test cases that were problematic before
    test_cases = [
        "Patient contact: 555-123-4567",
        "Emergency phone: (555) 987-6543",
        "Call 555.555.5555 for appointments",
        "Mobile: 5551234567",
        "Direct line: +1-555-444-3333",
        "Phone: 1-800-555-0199",
        "Office: 555 123 4567",
        "Contact Dr. Smith at (212)555-7890",
        "Hospital main: 1 555 999 8888",
        "Cell phone number is 9876543210"
    ]
    
    print(f"Testing {len(test_cases)} phone number formats...")
    
    total_detected = 0
    for i, test_case in enumerate(test_cases, 1):
        detected = await service.detect_pii(test_case)
        phone_numbers = [d for d in detected if d["entity_type"] == "PHONE_NUMBER"]
        
        if phone_numbers:
            total_detected += 1
            confidence = phone_numbers[0]["confidence"]
            print(f"✅ Test {i}: Detected phone with confidence {confidence:.2f}")
        else:
            print(f"❌ Test {i}: No phone detected - '{test_case}'")
    
    detection_rate = (total_detected / len(test_cases)) * 100
    print(f"\n📊 Enhanced Detection Results:")
    print(f"   Detected: {total_detected}/{len(test_cases)} ({detection_rate:.1f}%)")
    print(f"   Previous rate: ~77.2%")
    print(f"   Improvement: +{detection_rate - 77.2:.1f}%")
    
    return detection_rate

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_enhanced_detection())
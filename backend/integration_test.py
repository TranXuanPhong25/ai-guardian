#!/usr/bin/env python3
"""
Simple integration test to verify security improvements are working.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

def test_security_config():
    """Test security configuration."""
    print("Testing security configuration...")
    
    try:
        from app.security import security_config
        
        # Test that security config can be initialized
        assert security_config.secret_key is not None, "Secret key not configured"
        assert security_config.jwt_secret_key is not None, "JWT secret key not configured"
        assert len(security_config.allowed_hosts) > 0, "No allowed hosts configured"
        assert len(security_config.allowed_origins) > 0, "No allowed origins configured"
        
        print("✅ Security configuration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Security configuration test failed: {e}")
        return False

def test_input_validation():
    """Test input validation functions."""
    print("Testing input validation...")
    
    try:
        from app.security import validate_input_string, validate_file_path
        from fastapi import HTTPException
        
        # Test valid input
        result = validate_input_string("Hello World", "test_field")
        assert result == "Hello World", "Valid input should pass through"
        
        # Test invalid input (too long)
        try:
            validate_input_string("x" * 300, "test_field", max_length=255)
            assert False, "Should have raised HTTPException for long input"
        except HTTPException:
            pass  # Expected
        
        # Test empty input
        try:
            validate_input_string("", "test_field", allow_empty=False)
            assert False, "Should have raised HTTPException for empty input"
        except HTTPException:
            pass  # Expected
        
        # Test file path validation
        result = validate_file_path("valid/path/file.txt")
        assert result == "valid/path/file.txt", "Valid path should pass through"
        
        # Test dangerous path
        try:
            validate_file_path("../../../etc/passwd")
            assert False, "Should have raised HTTPException for dangerous path"
        except HTTPException:
            pass  # Expected
        
        print("✅ Input validation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Input validation test failed: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting components."""
    print("Testing rate limiting...")
    
    try:
        from app.rate_limiting import TokenBucket
        
        # Test token bucket
        bucket = TokenBucket(capacity=5, refill_rate=1.0)
        
        # Should be able to consume initial tokens
        assert bucket.consume(1), "Should be able to consume initial token"
        assert bucket.consume(4), "Should be able to consume remaining tokens"
        
        # Should not be able to consume more than capacity
        assert not bucket.consume(1), "Should not be able to consume more than capacity"
        
        print("✅ Rate limiting test passed")
        return True
        
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
        return False

def test_logging_config():
    """Test logging configuration."""
    print("Testing logging configuration...")
    
    try:
        from app.logging_config import get_logger, log_security_event
        
        # Test logger creation
        logger = get_logger("test_logger")
        assert logger is not None, "Logger should be created"
        
        # Test security event logging
        log_security_event("Test security event", level="INFO", test_data="test")
        
        print("✅ Logging configuration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Logging configuration test failed: {e}")
        return False

def test_file_validation():
    """Test file validation functions."""
    print("Testing file validation...")
    
    try:
        from app.api.routers.file import validate_file_security
        from fastapi import UploadFile, HTTPException
        from io import BytesIO
        
        # Mock UploadFile for testing
        class MockUploadFile:
            def __init__(self, filename, content_type=None, size=None):
                self.filename = filename
                self.content_type = content_type
                self.size = size
        
        # Test valid file
        valid_file = MockUploadFile("test.pdf", "application/pdf", 1024)
        try:
            validate_file_security(valid_file)
        except HTTPException:
            assert False, "Valid file should not raise exception"
        
        # Test invalid extension
        invalid_file = MockUploadFile("test.exe", "application/octet-stream", 1024)
        try:
            validate_file_security(invalid_file)
            assert False, "Invalid file should raise exception"
        except HTTPException:
            pass  # Expected
        
        # Test file too large
        large_file = MockUploadFile("test.pdf", "application/pdf", 100 * 1024 * 1024)
        try:
            validate_file_security(large_file)
            assert False, "Large file should raise exception"
        except HTTPException:
            pass  # Expected
        
        print("✅ File validation test passed")
        return True
        
    except Exception as e:
        print(f"❌ File validation test failed: {e}")
        return False

def test_agent_input_validation():
    """Test agent input validation."""
    print("Testing agent input validation...")
    
    try:
        from app.services.agents.agent_decision import process_query
        
        # Test normal input
        result = process_query("Hello, how are you?")
        assert result is not None, "Should return a result"
        
        # Test empty input
        result = process_query("")
        assert "output" in result, "Should return error message for empty input"
        
        # Test suspicious input
        result = process_query("<script>alert('test')</script>")
        assert "output" in result, "Should handle suspicious input safely"
        
        # Test very long input
        long_input = "x" * 20000
        result = process_query(long_input)
        assert "output" in result, "Should handle long input safely"
        
        print("✅ Agent input validation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Agent input validation test failed: {e}")
        return False

def main():
    """Run all integration tests."""
    print("Running AI Guardian Security Integration Tests")
    print("=" * 50)
    
    tests = [
        test_security_config,
        test_input_validation,
        test_rate_limiting,
        test_logging_config,
        test_file_validation,
        test_agent_input_validation,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("❌ Some tests failed. Please review the security implementation.")
        return 1
    else:
        print("✅ All security tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
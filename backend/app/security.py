"""
Security configuration and utilities for AI Guardian.
"""
import os
import secrets
import logging
from typing import List, Optional
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class SecurityConfig:
    """Security configuration settings."""
    
    def __init__(self):
        self.secret_key = self._get_secret_key()
        self.jwt_secret_key = self._get_jwt_secret()
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.allowed_hosts = self._get_allowed_hosts()
        self.allowed_origins = self._get_allowed_origins()
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", str(50 * 1024 * 1024)))  # 50MB default
        self.rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        
    def _get_secret_key(self) -> str:
        """Get or generate secret key."""
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            if self.environment == "production":
                raise ValueError("SECRET_KEY environment variable is required in production")
            logger.warning("SECRET_KEY not set, generating random key for development")
            secret_key = secrets.token_hex(32)
        return secret_key
    
    def _get_jwt_secret(self) -> str:
        """Get JWT secret key."""
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if not jwt_secret:
            if self.environment == "production":
                raise ValueError("JWT_SECRET_KEY environment variable is required in production")
            logger.warning("JWT_SECRET_KEY not set, using SECRET_KEY for development")
            jwt_secret = self.secret_key
        return jwt_secret
    
    def _get_allowed_hosts(self) -> List[str]:
        """Get allowed hosts list."""
        hosts = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(",")
        return [host.strip() for host in hosts if host.strip()]
    
    def _get_allowed_origins(self) -> List[str]:
        """Get allowed CORS origins."""
        origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
        return [origin.strip() for origin in origins if origin.strip()]
    
    def validate_environment(self) -> None:
        """Validate environment configuration."""
        required_vars = [
            "DATABASE_URL",
            "SUPABASE_URL", 
            "SUPABASE_ANON_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Production-specific validations
        if self.environment == "production":
            production_vars = ["SECRET_KEY", "JWT_SECRET_KEY"]
            missing_prod_vars = []
            for var in production_vars:
                if not os.getenv(var) or os.getenv(var) in ["your-secret-key-here", "your-jwt-secret"]:
                    missing_prod_vars.append(var)
            
            if missing_prod_vars:
                raise ValueError(f"Production requires secure values for: {', '.join(missing_prod_vars)}")
        
        logger.info(f"Security configuration validated for {self.environment} environment")

def validate_input_string(value: str, field_name: str, max_length: int = 255, allow_empty: bool = False) -> str:
    """Validate and sanitize string input."""
    if not allow_empty and (not value or not value.strip()):
        raise HTTPException(status_code=422, detail=f"{field_name} cannot be empty")
    
    if len(value) > max_length:
        raise HTTPException(status_code=422, detail=f"{field_name} is too long (max {max_length} characters)")
    
    # Basic sanitization - remove null bytes and control characters
    sanitized = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
    
    return sanitized.strip()

def validate_file_path(file_path: str) -> str:
    """Validate file path for security."""
    if not file_path:
        raise HTTPException(status_code=422, detail="File path cannot be empty")
    
    # Check for path traversal
    dangerous_patterns = ['../', '..\\', '/etc/', '/var/', '/usr/', 'c:\\']
    if any(pattern in file_path.lower() for pattern in dangerous_patterns):
        raise HTTPException(status_code=422, detail="Invalid file path detected")
    
    return file_path

# Global security configuration instance
security_config = SecurityConfig()
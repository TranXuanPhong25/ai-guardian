"""
Centralized logging configuration for AI Guardian.
"""
import os
import logging
import logging.handlers
from typing import Optional
from datetime import datetime

class SecurityAuditFilter(logging.Filter):
    """Filter for security-related log messages."""
    
    def filter(self, record):
        """Mark security-related log messages."""
        security_keywords = [
            'authentication', 'authorization', 'login', 'logout', 
            'password', 'token', 'secret', 'access_denied', 
            'security', 'vulnerability', 'attack', 'injection'
        ]
        
        message = record.getMessage().lower()
        if any(keyword in message for keyword in security_keywords):
            record.security_related = True
        else:
            record.security_related = False
            
        return True

class SanitizingFormatter(logging.Formatter):
    """Formatter that sanitizes log messages to prevent log injection."""
    
    def format(self, record):
        # Sanitize the log message
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            # Remove potential log injection characters
            record.msg = record.msg.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        
        # Add security marking if present
        if hasattr(record, 'security_related') and record.security_related:
            record.levelname = f"SECURITY-{record.levelname}"
        
        return super().format(record)

def setup_logging(
    level: str = None,
    log_file: str = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Setup centralized logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        max_file_size: Maximum log file size in bytes
        backup_count: Number of backup log files to keep
    """
    # Get logging level from environment or parameter
    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = SanitizingFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = SanitizingFormatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(simple_formatter)
    console_handler.addFilter(SecurityAuditFilter())
    
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        try:
            # Ensure log directory exists
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            # Create rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(detailed_formatter)
            file_handler.addFilter(SecurityAuditFilter())
            
            root_logger.addHandler(file_handler)
            
        except Exception as e:
            # If file logging fails, log to console
            logging.error(f"Failed to setup file logging: {e}")
    
    # Security-specific logger
    security_logger = logging.getLogger('security')
    security_log_file = os.getenv("SECURITY_LOG_FILE")
    
    if security_log_file:
        try:
            security_handler = logging.handlers.RotatingFileHandler(
                security_log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            security_handler.setLevel(logging.WARNING)
            security_handler.setFormatter(detailed_formatter)
            
            # Only log security-related messages to this file
            security_filter = SecurityAuditFilter()
            security_handler.addFilter(lambda record: security_filter.filter(record) and record.security_related)
            
            security_logger.addHandler(security_handler)
            
        except Exception as e:
            logging.error(f"Failed to setup security logging: {e}")
    
    # Log configuration details
    logging.info(f"Logging configured - Level: {log_level}, File: {log_file or 'Console only'}")
    
    # Test security logging
    security_logger.warning("Security logging initialized")

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)

def log_security_event(message: str, level: str = "WARNING", **kwargs) -> None:
    """Log a security-related event."""
    security_logger = logging.getLogger('security')
    
    # Add context information
    context = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': 'security',
        **kwargs
    }
    
    # Format message with context
    formatted_message = f"{message} | Context: {context}"
    
    log_level = getattr(logging, level.upper(), logging.WARNING)
    security_logger.log(log_level, formatted_message)

def log_auth_event(user_id: Optional[str], action: str, success: bool, **kwargs) -> None:
    """Log authentication/authorization events."""
    status = "SUCCESS" if success else "FAILURE"
    message = f"AUTH {status}: User {user_id or 'Unknown'} - {action}"
    
    log_security_event(
        message,
        level="INFO" if success else "WARNING",
        user_id=user_id,
        action=action,
        success=success,
        **kwargs
    )

def log_file_operation(user_id: Optional[str], operation: str, filename: str, success: bool, **kwargs) -> None:
    """Log file operations for security auditing."""
    status = "SUCCESS" if success else "FAILURE"
    message = f"FILE {status}: User {user_id or 'Unknown'} - {operation} - {filename}"
    
    log_security_event(
        message,
        level="INFO" if success else "WARNING",
        user_id=user_id,
        operation=operation,
        filename=filename,
        success=success,
        **kwargs
    )

# Initialize logging when module is imported
def init_logging():
    """Initialize logging with environment-based configuration."""
    log_file = os.getenv("LOG_FILE")
    if not log_file and os.getenv("ENVIRONMENT") != "development":
        # Default log file for production
        log_file = "/var/log/ai-guardian/app.log"
    
    setup_logging(log_file=log_file)

# Auto-initialize if not in test environment
if not os.getenv("TESTING"):
    init_logging()
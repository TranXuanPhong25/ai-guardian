"""
Rate limiting middleware for AI Guardian API.
"""
import time
import asyncio
from typing import Dict, Optional
from collections import defaultdict, deque
import logging
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

class TokenBucket:
    """Token bucket implementation for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket."""
        now = time.time()
        
        # Refill tokens based on elapsed time
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using token bucket algorithm."""
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: int = 10,
        cleanup_interval: int = 300  # 5 minutes
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        
        # Storage for rate limiting data
        self.buckets: Dict[str, TokenBucket] = {}
        self.last_cleanup = time.time()
        self.cleanup_interval = cleanup_interval
        
        # Track suspicious activity
        self.blocked_attempts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
    def _get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for client (IP + User ID if available)."""
        client_ip = request.client.host if request.client else "unknown"
        
        # Try to get user ID from authentication
        user_id = None
        if hasattr(request.state, 'user') and request.state.user:
            user_id = getattr(request.state.user, 'id', None)
        
        return f"{client_ip}:{user_id or 'anonymous'}"
    
    def _cleanup_old_buckets(self):
        """Remove old, unused token buckets to prevent memory leaks."""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        # Remove buckets that haven't been used recently
        cutoff_time = now - self.cleanup_interval
        to_remove = []
        
        for client_id, bucket in self.buckets.items():
            if bucket.last_refill < cutoff_time:
                to_remove.append(client_id)
        
        for client_id in to_remove:
            del self.buckets[client_id]
        
        # Cleanup blocked attempts
        for client_id in list(self.blocked_attempts.keys()):
            attempts = self.blocked_attempts[client_id]
            # Remove attempts older than 1 hour
            while attempts and attempts[0] < now - 3600:
                attempts.popleft()
            
            if not attempts:
                del self.blocked_attempts[client_id]
        
        self.last_cleanup = now
        logger.debug(f"Rate limit cleanup: removed {len(to_remove)} old buckets")
    
    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from rate limiting."""
        exempt_paths = [
            "/health",
            "/metrics", 
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        return any(path.startswith(exempt) for exempt in exempt_paths)
    
    def _get_rate_limit_for_endpoint(self, request: Request) -> tuple[int, int]:
        """Get specific rate limits for different endpoints."""
        path = request.url.path
        method = request.method
        
        # More restrictive limits for sensitive endpoints
        if "/file/upload" in path:
            return 10, 5  # 10 per minute, burst of 5
        elif "/extract" in path:
            return 20, 5  # 20 per minute, burst of 5
        elif "/chat" in path:
            return 100, 20  # 100 per minute, burst of 20
        elif method == "POST":
            return 30, 10  # 30 per minute, burst of 10 for POST requests
        else:
            return self.requests_per_minute, self.burst_size
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for exempt paths
        if self._is_exempt_path(request.url.path):
            return await call_next(request)
        
        # Cleanup old data periodically
        self._cleanup_old_buckets()
        
        client_id = self._get_client_identifier(request)
        requests_per_minute, burst_size = self._get_rate_limit_for_endpoint(request)
        
        # Get or create token bucket for this client
        if client_id not in self.buckets:
            refill_rate = requests_per_minute / 60.0
            self.buckets[client_id] = TokenBucket(burst_size, refill_rate)
        
        bucket = self.buckets[client_id]
        
        # Try to consume a token
        if bucket.consume():
            # Request allowed
            try:
                response = await call_next(request)
                
                # Add rate limit headers
                response.headers["X-RateLimit-Limit"] = str(requests_per_minute)
                response.headers["X-RateLimit-Remaining"] = str(int(bucket.tokens))
                response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
                
                return response
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                raise
        else:
            # Request blocked due to rate limiting
            self.blocked_attempts[client_id].append(time.time())
            
            # Log security event for potential abuse
            logger.warning(
                f"Rate limit exceeded for client {client_id} on {request.url.path}",
                extra={'security_related': True}
            )
            
            # Check for potential abuse (many blocked attempts)
            recent_blocks = len([
                attempt for attempt in self.blocked_attempts[client_id]
                if attempt > time.time() - 300  # last 5 minutes
            ])
            
            if recent_blocks > 20:
                logger.warning(
                    f"Suspicious activity: {recent_blocks} blocked attempts from {client_id}",
                    extra={'security_related': True}
                )
            
            # Return rate limit error
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {requests_per_minute} per minute",
                    "retry_after": int(60 / (requests_per_minute / 60.0))
                },
                headers={
                    "X-RateLimit-Limit": str(requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + 60)),
                    "Retry-After": str(int(60 / (requests_per_minute / 60.0)))
                }
            )

def get_rate_limit_middleware(
    requests_per_minute: int = None,
    burst_size: int = None
) -> RateLimitMiddleware:
    """Factory function to create rate limit middleware with configuration."""
    import os
    
    rpm = requests_per_minute or int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    burst = burst_size or int(os.getenv("RATE_LIMIT_BURST_SIZE", "10"))
    
    return RateLimitMiddleware(
        app=None,  # Will be set by FastAPI
        requests_per_minute=rpm,
        burst_size=burst
    )
import os

# import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from starlette.middleware.sessions import SessionMiddleware

from app.api.routers import chat, file, mask, ai, health
from app.config import Config
from app.security import security_config
from app.rate_limiting import get_rate_limit_middleware
from app.database.database import engine, Base
from app.models import chat_session, mask_mapping, rag_document, message, pii_mapping, file as file_models, profile
_ = load_dotenv(find_dotenv()) # read local .env file

config = Config()

# Validate security configuration
security_config.validate_environment()

# TODO: remove
# genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

def create_tables():
    chat_session.Base.metadata.create_all(bind=engine)
    message.Base.metadata.create_all(bind=engine)
    file_models.Base.metadata.create_all(bind=engine)
    profile.Base.metadata.create_all(bind=engine)
    # notification.Base.metadata.create_all(bind=engine)
    mask_mapping.Base.metadata.create_all(bind=engine)
    rag_document.Base.metadata.create_all(bind=engine)
    pii_mapping.Base.metadata.create_all(bind=engine)
    

app = FastAPI(
    title="AI Guardian API",
    description="Secure AI Conversation Platform",
    version="1.0.0",
    docs_url="/docs" if security_config.environment != "production" else None,
    redoc_url="/redoc" if security_config.environment != "production" else None
)

# Security middleware - order matters!
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"] if security_config.environment == "development" else security_config.allowed_hosts
)

app.add_middleware(
    SessionMiddleware,
    secret_key=security_config.secret_key,
    max_age=3600,  # 1 hour
    same_site="lax",
    https_only=security_config.environment == "production"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=security_config.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add rate limiting middleware
rate_limit_middleware = get_rate_limit_middleware()
app.add_middleware(rate_limit_middleware.__class__, **rate_limit_middleware.__dict__)

from contextlib import asynccontextmanager
from fastapi import Request
from fastapi.responses import Response

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    
    return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield

app.router.lifespan_context = lifespan

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(file.router)
app.include_router(mask.router)
app.include_router(ai.router)
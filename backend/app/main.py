import os

# import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import chat, file, mask, ai
from app.config import Config
from app.database.database import engine, Base
from app.models import chat_session, mask_mapping, rag_document, message, pii_mapping, file as file_models, profile
_ = load_dotenv(find_dotenv()) # read local .env file

config = Config()
# Configure Gemini API
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
    

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield

app.router.lifespan_context = lifespan

app.include_router(chat.router)
app.include_router(file.router)
app.include_router(mask.router)
app.include_router(ai.router)
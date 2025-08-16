import os
import google.generativeai as genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import status
from fastapi import Depends
from fastapi import APIRouter
from fastapi import Response
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import BackgroundTasks
from fastapi import UploadFile, File
from fastapi import Form
from fastapi import File as FastAPIFile
from fastapi import Query
from fastapi import Path
from fastapi import Body
from fastapi import Cookie
from fastapi import Header
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import status
from fastapi import Depends
from fastapi import APIRouter
from fastapi import Response
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import BackgroundTasks
from fastapi import UploadFile, File
from fastapi import Form
from fastapi import File as FastAPIFile
from fastapi import Query
from fastapi import Path
from fastapi import Body
from fastapi import Cookie
from fastapi import Header
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware
import os
import google.generativeai as genai
from app.api.routers import chat, user, file, mask, ai
from app.database.database import engine
from app.models import profile, chat_session, message
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv()) # read local .env file

# Configure Gemini API
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

def create_tables():
    profile.Base.metadata.create_all(bind=engine)
    chat_session.Base.metadata.create_all(bind=engine)
    message.Base.metadata.create_all(bind=engine)

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

app.include_router(user.router)
app.include_router(chat.router)
app.include_router(file.router)
app.include_router(mask.router)
app.include_router(ai.router)
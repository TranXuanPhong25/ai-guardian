from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.routers.mask import mask_content
from app.database.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse, MessageResponse, ChatSessionResponse, UpdateTitleRequest, ChatRequestWithFiles
from app.schemas.mask import MaskRequest
from app.services import chat_service
from app.services.chat_service import process_chat
from app.services.extraction_service import file_extractor_service
from app.services.masking_service import PIIMaskerService
from app.dependencies import verify_jwt
from app.models import ChatSession, Message, MessageFile, File
from uuid import UUID
from datetime import datetime
import os
import json
from app.services.agents.rag_agent import DocumentRAG
from app.config import Config

config = Config()
rag = DocumentRAG(config)
router = APIRouter(prefix="/api")

# route to get all messages of a session
@router.get("/sessions/{session_id}", response_model=list[MessageResponse])
async def get_chat_history(session_id: UUID, user=Depends(verify_jwt), db: Session = Depends(get_db)):
    # Retrieve the chat session and verify the user
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id,
                                                ChatSession.user_id == user.user.id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Retrieve all messages in this session with their attached files
    messages = db.query(Message).filter(Message.chat_session_id == session_id).order_by(Message.created_at.asc()).all()
    
    # Build response with file attachments
    response_messages = []
    for message in messages:
        # Get attached files for this message
        attached_files = []
        for message_file in message.attached_files:
            attached_files.append({
                "file_id": message_file.file.file_id,
                "filename": message_file.file.filename,
                "file_path": message_file.file.file_path
            })
        
        response_messages.append(MessageResponse(
            id=message.id,
            chat_session_id=message.chat_session_id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
            attached_files=attached_files
        ))
    
    return response_messages


# route to post a message to a session or start a new session
@router.post("/sessions/{session_id}", response_model=ChatResponse)
async def continue_chat(
    session_id: UUID,
    request: ChatRequestWithFiles,
    user=Depends(verify_jwt),
    db: Session = Depends(get_db)
):
    # Initialize services
    pii_masker_service = PIIMaskerService()
    
    # Verify the session belongs to the user
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id,
                                                ChatSession.user_id == user.user.id).first()
    if not chat_session:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        title = f"New Chat - {current_time}"

        chat_session = ChatSession(id=session_id, user_id=user.user.id, title=title)
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)

    user_message = request.messages[-1].content if request.messages else ""

    # Update the updated_at timestamp
    if chat_session:
        chat_session.updated_at = datetime.utcnow()

    # Add the user's new message to the session
    message_obj = Message(
        chat_session_id=chat_session.id,
        role="user",
        content=user_message
    )
    db.add(message_obj)
    db.commit()
    db.refresh(message_obj)

    # Handle file URLs and text extraction
    uploaded_files = []
    extracted_text_content = ""
    
    if request.fileUrls:
        all_extracted_text = []
        
        for file_url in request.fileUrls:
            try:
                # Get file from database by URL
                file_obj = db.query(File).filter(File.file_path == file_url, 
                                                File.user_id == user.user.id).first()
                if not file_obj:
                    print(f"File not found for URL: {file_url}")
                    continue

                # Associate file with message
                message_file = MessageFile(
                    message_id=message_obj.id,
                    file_id=file_obj.file_id
                )
                db.add(message_file)
                uploaded_files.append(file_obj)

                # Use already extracted text or extract if needed
                if file_obj.extracted_text:
                    all_extracted_text.append(f"From file '{file_obj.filename}':\n{file_obj.extracted_text}")
                else:
                    # Extract text from the file
                    try:
                        file_extension = os.path.splitext(file_obj.filename)[1]
                        print(f"Extracting text from file {file_obj.filename} with extension {file_extension}")
                        extracted_text = file_extractor_service.extract_text(file_url, file_extension)
                        if extracted_text:
                            # Save extracted text to database
                            file_obj.extracted_text = extracted_text
                            all_extracted_text.append(f"From file '{file_obj.filename}':\n{extracted_text}")
                            rag.ingest_file(extracted_text, file_url)
                    except Exception as e:
                        print(f"Error extracting text from file {file_obj.filename}: {str(e)}")

            except Exception as e:
                print(f"Error processing file URL {file_url}: {str(e)}")
                # Continue with chat even if file processing fails

        # Combine all extracted text
        if all_extracted_text:
            extracted_text_content = "\n\n---\n\n".join(all_extracted_text)
        extracted_text_content = extracted_text_content.strip()

    db.commit()

    # Prepare content for masking (user message + file context)
    content_to_mask = user_message
    if extracted_text_content:
        content_to_mask += f"\n\n\nFile context:\n{extracted_text_content}"
    mapping = {}
    # Mask the combined content (user message + extracted text from files)
    try:
        mask_request = MaskRequest(session_id=str(session_id), content=content_to_mask)
        mask_result = await mask_content(mask_request, db)
        masked_text = mask_result["masked_text"]
        mapping = mask_result["mapping"]
        
        # Use masked content for processing
        processing_content = masked_text
    except Exception as e:
        print(f"Error masking content: {str(e)}")
        # If masking fails, use original content
        processing_content = content_to_mask

    # Create chat messages for processing with RAG context
    chat_messages = [{"role": "user", "content": processing_content}]
    
    return await process_chat(request.model, chat_messages, db, session_id, mapping)


# route to get all chat sessions
@router.get("/sessions", response_model=list[ChatSessionResponse])
async def get_all_chat_sessions(user=Depends(verify_jwt), db: Session = Depends(get_db)):
    chat_sessions = db.query(ChatSession).filter(ChatSession.user_id == user.user.id).order_by(
        ChatSession.updated_at.desc()).all()
    return chat_sessions


# route to update title for a chat sessions
@router.patch("/sessions/{session_id}/title", response_model=ChatSessionResponse)
async def update_chat_session_title(
        session_id: UUID,
        title_request: UpdateTitleRequest,
        user=Depends(verify_jwt),
        db: Session = Depends(get_db)
):
    # Retrieve the chat session and verify the user
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id,
                                                ChatSession.user_id == user.user.id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Update the title
    chat_session.title = title_request.title
    db.commit()
    db.refresh(chat_session)

    return chat_session


# route to delete a chat session and all its messages
@router.delete("/sessions/{session_id}", response_model=dict)
async def delete_chat_session(
        session_id: UUID,
        user=Depends(verify_jwt),
        db: Session = Depends(get_db)
):
    # Retrieve the chat session and verify the user
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id,
                                                ChatSession.user_id == user.user.id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Delete all messages associated with the chat session
    db.query(Message).filter(Message.chat_session_id == session_id).delete()

    # Delete the chat session
    db.delete(chat_session)
    db.commit()

    return {"detail": "Chat session and its messages have been deleted"}


# route to empty chat session and messages table (only used via curl / Postman or any API tool)
@router.delete("/empty-sessions", response_model=dict)
async def empty_chat_sessions_and_messages(
        db: Session = Depends(get_db)
):
    # Delete all messages from the database
    db.query(Message).delete()

    # Delete all chat sessions from the database
    db.query(ChatSession).delete()

    db.commit()

    return {"detail": "All chat sessions and messages have been deleted"}

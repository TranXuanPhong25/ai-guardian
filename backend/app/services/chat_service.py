# Hàm phát hiện thông tin nhạy cảm (mock, có thể thay thế bằng AI thực tế)
from app.services.agents.agent_decision import process_query
import concurrent.futures
import functools

from sqlalchemy.orm import Session
import asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from app.models import Message
from app.services.unmasking_service import pii_unmasker_service
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
import os

import os

# Create thread pool for blocking operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

async def process_query_async(query: str) -> dict:
    """Async wrapper for process_query to prevent blocking."""
    loop = asyncio.get_event_loop()
    try:
        # Run process_query in thread pool to avoid blocking
        result = await loop.run_in_executor(thread_pool, process_query, query)
        return result
    except Exception as e:
        print(f"Error in async process_query: {str(e)}")
        return {"output": f"I apologize, but I encountered an error while processing your request. Please try rephrasing your question."}

async def process_chat(model_id: str, messages: list, db: Session, session_id: str, mapping: dict = None):

    # Extract content from messages array
    if isinstance(messages, list) and len(messages) > 0:
        last_message = messages[-1]
        if isinstance(last_message, dict):
            current_message_content = last_message.get('content', '')
        else:
            current_message_content = str(last_message)
    else:
        current_message_content = str(messages)
    
    print(f"Processing chat with model {model_id} and message: {current_message_content}")

    # Get response from agent decision system with error handling
    try:
        agent_result = await process_query_async(current_message_content)
    except Exception as e:
        print(f"Error in process_query: {str(e)}")
        # Fallback to simple response
        agent_result = {"output": f"I apologize, but I encountered an error while processing your request. Please try rephrasing your question."}
    
    # Extract response content from the agent result
    response_content = ""
    
    if isinstance(agent_result, dict):
        # Try to get output first
        if "output" in agent_result and agent_result["output"]:
            output = agent_result["output"]
            if hasattr(output, 'content'):
                response_content = output.content
            else:
                response_content = str(output)
        
        # If no output, try to get from messages
        elif "messages" in agent_result and agent_result["messages"]:
            if isinstance(agent_result["messages"], list):
                # Get the last message
                last_message = agent_result["messages"][-1]
                if hasattr(last_message, 'content'):
                    response_content = last_message.content
                else:
                    response_content = str(last_message)
            else:
                # Single message
                if hasattr(agent_result["messages"], 'content'):
                    response_content = agent_result["messages"].content
                else:
                    response_content = str(agent_result["messages"])
    
    # Fallback if we couldn't extract content
    if not response_content:
        response_content = str(agent_result)
    
    # Clean up response content for better streaming
    response_content = response_content.strip()
    if not response_content:
        response_content = "I'm sorry, I couldn't generate a proper response. Please try asking again."
    
    # Handle special characters and formatting for better streaming
    # Keep line breaks but normalize multiple consecutive ones
    response_content = response_content.replace('\n\n\n', '\n\n')  # Reduce triple+ line breaks to double
    # Don't remove all line breaks - preserve paragraph structure
    # TODO: UNMASK here
    if mapping:
        response_content = pii_unmasker_service.unmask_text(response_content,mapping)

    
    # Save the assistant's response to database
    assistant_message = Message(
        chat_session_id=session_id,
        role="assistant",
        content=response_content
    )
    db.add(assistant_message)
    db.commit()
    
    # Create streaming response
    async def generate_response():
        import asyncio
        
        # Determine streaming strategy based on content length
        if len(response_content) < 50:
            # Short responses: stream faster
            chunk_size = 3
            delay = 0.03
        elif len(response_content) < 200:
            # Medium responses: moderate speed
            chunk_size = 2
            delay = 0.05
        else:
            # Long responses: slower for readability
            chunk_size = 2
            delay = 0.07
        
        # Stream the response more smoothly
        # Split by paragraphs first (double line breaks), then by sentences
        paragraphs = response_content.split('\n\n')
        
        for para_idx, paragraph in enumerate(paragraphs):
            if paragraph.strip():  # Skip empty paragraphs
                if para_idx > 0:
                    # Add paragraph break
                    yield f'0:"\\n\\n"\n'
                
                # Split paragraph by sentences for natural breaks
                sentences = paragraph.replace('!', '.').replace('?', '.').split('. ')
                
                for sentence_idx, sentence in enumerate(sentences):
                    if sentence.strip():  # Skip empty sentences
                        if sentence_idx > 0:
                            # Add period back except for last sentence
                            yield f'0:"."\n'
                            yield f'0:" "\n'  # Space after period
                        
                        # Check if sentence contains single line breaks
                        if '\n' in sentence:
                            # Handle single line breaks within sentence
                            parts = sentence.split('\n')
                            for part_idx, part in enumerate(parts):
                                if part.strip():
                                    if part_idx > 0:
                                        yield f'0:"\\n"\n'  # Single line break
                                    
                                    # Stream the part in chunks
                                    words = part.strip().split()
                                    for i in range(0, len(words), chunk_size):
                                        chunk_words = words[i:i + chunk_size]
                                        chunk_text = ' '.join(chunk_words)
                                        
                                        # Escape quotes for JSON
                                        escaped_chunk = chunk_text.replace('"', '\\"')
                                        yield f'0:"{escaped_chunk}"\n'
                                        
                                        # Add space after chunk (except for last chunk in part)
                                        if i + chunk_size < len(words):
                                            yield f'0:" "\n'
                                        
                                        # Async delay for smooth streaming effect
                                        await asyncio.sleep(delay)
                        else:
                            # For sentence without line breaks, stream in chunks
                            words = sentence.strip().split()
                            
                            for i in range(0, len(words), chunk_size):
                                chunk_words = words[i:i + chunk_size]
                                chunk_text = ' '.join(chunk_words)
                                
                                # Escape quotes for JSON
                                escaped_chunk = chunk_text.replace('"', '\\"')
                                yield f'0:"{escaped_chunk}"\n'
                                
                                # Add space after chunk (except for last chunk in sentence)
                                if i + chunk_size < len(words):
                                    yield f'0:" "\n'
                                
                                # Async delay for smooth streaming effect
                                await asyncio.sleep(delay)
        
        # Add final period if the response doesn't end with punctuation
        if response_content and not response_content.strip().endswith(('.', '!', '?', ':')):
            yield f'0:"."\n'
    
    response = StreamingResponse(generate_response(), media_type="text/plain")
    response.headers["x-vercel-ai-data-stream"] = "v1"
    return response
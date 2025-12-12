"""
Path: backend/src/api/routes/chat.py
Version: 2

Changes in v2:
- Call validate_conversation_access() BEFORE starting SSE stream
- This ensures 404/403 errors are returned as HTTP status codes, not in stream
- Fixes issue where all errors were returned as 200 with error in stream

Chat streaming endpoint
Provides Server-Sent Events (SSE) streaming for chat completions
"""

import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from src.models.chat import ChatRequest
from src.services.chat_service import ChatService
from src.api.deps import get_database, UserFromRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    current_user: UserFromRequest,
    db = Depends(get_database)
) -> StreamingResponse:
    """
    Stream chat completion
    
    Streams LLM response using Server-Sent Events (SSE).
    
    Request body:
    - **message**: User message content (required, 1-50000 chars)
    - **conversationId**: Conversation ID for context (required)
    - **promptCustomization**: Optional user-specific prompt customization
    
    Response:
    - Content-Type: text/event-stream
    - Format: "data: {chunk}\\n\\n" for each chunk
    - Final: "data: [DONE]\\n\\n"
    
    Returns:
    - 200 OK: Streaming started
    - 400 Bad Request: Invalid request (missing conversationId, etc.)
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: Access denied to conversation
    - 404 Not Found: Conversation not found
    - 500 Internal Server Error: Streaming error
    
    Requires authentication and access to conversation.
    
    Example:
        POST /api/chat/stream
        {
            "message": "Hello!",
            "conversationId": "conv-123",
            "promptCustomization": "Be concise"
        }
        
        Response (SSE stream):
        data: Hello
        data:  there
        data: ! How
        data:  can I help?
        data: [DONE]
    """
    chat_service = ChatService(db=db)
    
    # Validate conversation access BEFORE starting SSE stream
    # This ensures 404/403 errors are raised as HTTP exceptions
    # instead of being caught in the stream generator
    chat_service.validate_conversation_access(
        conversation_id=request.conversation_id,
        current_user=current_user
    )
    
    async def generate():
        """Generate SSE stream from chat service"""
        try:
            async for chunk in chat_service.stream_chat(
                message=request.message,
                conversation_id=request.conversation_id,
                current_user=current_user,
                prompt_customization=request.prompt_customization
            ):
                # Format as SSE
                yield f"data: {chunk}\n\n"
            
            # Send completion signal
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Stream generation error: {e}")
            # Send error signal
            yield f"data: [ERROR: {str(e)}]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
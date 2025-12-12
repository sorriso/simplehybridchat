"""
Path: backend/src/api/routes/conversations.py
Version: 3

Conversation management endpoints

Changes in v3:
- Fixed UserFromRequest usage: removed duplicate Depends()
- Changed from: current_user: UserFromRequest = Depends()
- Changed to: current_user: UserFromRequest

Changes in v2:
- Added GET /api/conversations/{id}/messages endpoint
"""

from typing import Optional
from fastapi import APIRouter, Depends, status

from src.models.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ShareConversationRequest,
    UnshareConversationRequest
)
from src.models.message import MessageResponse
from src.models.responses import (
    EmptyResponse,
    ConversationListResponse,
    SingleConversationResponse,
    MessageListResponse
)
from src.services.conversation_service import ConversationService
from src.services.message_service import MessageService
from src.api.deps import get_database, UserFromRequest


router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("", response_model=SingleConversationResponse[ConversationResponse], status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: UserFromRequest,
    db = Depends(get_database)
) -> SingleConversationResponse[ConversationResponse]:
    """
    Create new conversation
    
    Creates a new conversation owned by the authenticated user.
    
    Request body:
    - **title**: Conversation title (default: "New Conversation")
    - **group_id**: Group ID (optional, null if not grouped)
    
    Returns:
    - 201 Created: Conversation created
    - 401 Unauthorized: Invalid token
    - 404 Not Found: Group not found
    
    Requires authentication.
    """
    conversation_service = ConversationService(db=db)
    conversation = conversation_service.create_conversation(conversation_data, current_user)
    
    return SingleConversationResponse(conversation=conversation)


@router.get("", response_model=ConversationListResponse[ConversationResponse])
async def list_conversations(
    current_user: UserFromRequest,
    db = Depends(get_database)
) -> ConversationListResponse[ConversationResponse]:
    """
    List user's conversations
    
    Returns all conversations owned by the authenticated user.
    Sorted by updatedAt DESC (most recent first).
    
    Returns:
    - 200 OK: List of conversations
    - 401 Unauthorized: Invalid token
    
    Requires authentication.
    """
    conversation_service = ConversationService(db=db)
    conversations = conversation_service.list_conversations(current_user)
    
    return ConversationListResponse(conversations=conversations)


@router.get("/shared", response_model=ConversationListResponse[ConversationResponse])
async def list_shared_conversations(
    current_user: UserFromRequest,
    db = Depends(get_database)
) -> ConversationListResponse[ConversationResponse]:
    """
    List shared conversations
    
    Returns conversations shared with the authenticated user's groups.
    
    Returns:
    - 200 OK: List of shared conversations
    - 401 Unauthorized: Invalid token
    
    Requires authentication.
    """
    conversation_service = ConversationService(db=db)
    conversations = conversation_service.list_shared_conversations(current_user)
    
    return ConversationListResponse(conversations=conversations)


@router.get("/{conversation_id}", response_model=SingleConversationResponse[ConversationResponse])
async def get_conversation(
    conversation_id: str,
    current_user: UserFromRequest,
    db = Depends(get_database)
) -> SingleConversationResponse[ConversationResponse]:
    """
    Get conversation by ID
    
    Returns conversation details. User must be owner or have shared access.
    
    Path parameters:
    - **conversation_id**: Conversation ID
    
    Returns:
    - 200 OK: Conversation data
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: Access denied
    - 404 Not Found: Conversation not found
    
    Requires authentication.
    """
    conversation_service = ConversationService(db=db)
    conversation = conversation_service.get_conversation(conversation_id, current_user)
    
    return SingleConversationResponse(conversation=conversation)


@router.get("/{conversation_id}/messages", response_model=MessageListResponse[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    current_user: UserFromRequest,
    db = Depends(get_database)
) -> MessageListResponse[MessageResponse]:
    """
    Get conversation messages
    
    Returns all messages in a conversation. User must be owner or have shared access.
    Messages are sorted chronologically (oldest first).
    
    Path parameters:
    - **conversation_id**: Conversation ID
    
    Returns:
    - 200 OK: List of messages
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: Access denied
    - 404 Not Found: Conversation not found
    
    Requires authentication.
    """
    message_service = MessageService(db=db)
    messages = message_service.get_conversation_messages(conversation_id, current_user)
    
    return MessageListResponse(messages=messages)


@router.put("/{conversation_id}", response_model=SingleConversationResponse[ConversationResponse])
async def update_conversation(
    conversation_id: str,
    updates: ConversationUpdate,
    current_user: UserFromRequest,
    db = Depends(get_database)
) -> SingleConversationResponse[ConversationResponse]:
    """
    Update conversation
    
    Updates conversation title and/or group. Only owner can update.
    
    Path parameters:
    - **conversation_id**: Conversation ID
    
    Request body (all optional):
    - **title**: New title
    - **group_id**: New group ID (null to ungroup)
    
    Returns:
    - 200 OK: Conversation updated
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: Not owner
    - 404 Not Found: Conversation not found
    
    Requires authentication. Owner only.
    """
    conversation_service = ConversationService(db=db)
    conversation = conversation_service.update_conversation(conversation_id, updates, current_user)
    
    return SingleConversationResponse(conversation=conversation)


@router.delete("/{conversation_id}", response_model=EmptyResponse)
async def delete_conversation(
    conversation_id: str,
    current_user: UserFromRequest,
    db = Depends(get_database)
) -> EmptyResponse:
    """
    Delete conversation
    
    Permanently deletes a conversation and all its messages. Only owner can delete.
    
    Path parameters:
    - **conversation_id**: Conversation ID
    
    Returns:
    - 200 OK: Conversation deleted
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: Not owner
    - 404 Not Found: Conversation not found
    
    Requires authentication. Owner only.
    """
    conversation_service = ConversationService(db=db)
    conversation_service.delete_conversation(conversation_id, current_user)
    
    return EmptyResponse(message="Conversation deleted successfully")


@router.post("/{conversation_id}/share", response_model=SingleConversationResponse[ConversationResponse])
async def share_conversation(
    conversation_id: str,
    share_data: ShareConversationRequest,
    current_user: UserFromRequest,
    db = Depends(get_database)
) -> SingleConversationResponse[ConversationResponse]:
    """
    Share conversation with groups
    
    Shares conversation with specified groups. Members of these groups
    can view the conversation (read-only). Only owner can share.
    
    Path parameters:
    - **conversation_id**: Conversation ID
    
    Request body:
    - **group_ids**: List of group IDs to share with
    
    Returns:
    - 200 OK: Conversation shared
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: Not owner
    - 404 Not Found: Conversation not found
    
    Requires authentication. Owner only.
    """
    conversation_service = ConversationService(db=db)
    conversation = conversation_service.share_conversation(conversation_id, share_data, current_user)
    
    return SingleConversationResponse(conversation=conversation)


@router.post("/{conversation_id}/unshare", response_model=SingleConversationResponse[ConversationResponse])
async def unshare_conversation(
    conversation_id: str,
    unshare_data: UnshareConversationRequest,
    current_user: UserFromRequest,
    db = Depends(get_database)
) -> SingleConversationResponse[ConversationResponse]:
    """
    Unshare conversation from groups
    
    Removes sharing for specified groups. Only owner can unshare.
    
    Path parameters:
    - **conversation_id**: Conversation ID
    
    Request body:
    - **group_ids**: List of group IDs to unshare from
    
    Returns:
    - 200 OK: Conversation unshared
    - 401 Unauthorized: Invalid token
    - 403 Forbidden: Not owner
    - 404 Not Found: Conversation not found
    
    Requires authentication. Owner only.
    """
    conversation_service = ConversationService(db=db)
    conversation = conversation_service.unshare_conversation(conversation_id, unshare_data, current_user)
    
    return SingleConversationResponse(conversation=conversation)
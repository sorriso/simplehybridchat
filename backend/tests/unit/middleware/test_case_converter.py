"""
Path: backend/tests/middleware/test_case_converter.py
Version: 1

Tests for snake_case to camelCase converter
Run with: pytest tests/test_case_converter.py -v
"""

import pytest
from src.core.case_converter import (
    snake_to_camel,
    camel_to_snake,
    convert_dict_keys_to_camel,
    convert_dict_keys_to_snake
)


class TestSnakeToCamel:
    """Test snake_case to camelCase conversion"""
    
    def test_simple_conversion(self):
        assert snake_to_camel('user_id') == 'userId'
        assert snake_to_camel('created_at') == 'createdAt'
        assert snake_to_camel('updated_at') == 'updatedAt'
    
    def test_multiple_words(self):
        assert snake_to_camel('shared_with_group_ids') == 'sharedWithGroupIds'
        assert snake_to_camel('prompt_customization') == 'promptCustomization'
        assert snake_to_camel('message_count') == 'messageCount'
    
    def test_no_underscores(self):
        assert snake_to_camel('id') == 'id'
        assert snake_to_camel('name') == 'name'
        assert snake_to_camel('email') == 'email'


class TestCamelToSnake:
    """Test camelCase to snake_case conversion"""
    
    def test_simple_conversion(self):
        assert camel_to_snake('userId') == 'user_id'
        assert camel_to_snake('createdAt') == 'created_at'
        assert camel_to_snake('updatedAt') == 'updated_at'
    
    def test_multiple_words(self):
        assert camel_to_snake('sharedWithGroups') == 'shared_with_groups'
        assert camel_to_snake('promptCustomization') == 'prompt_customization'
        assert camel_to_snake('messageCount') == 'message_count'
    
    def test_no_capitals(self):
        assert camel_to_snake('id') == 'id'
        assert camel_to_snake('name') == 'name'
        assert camel_to_snake('email') == 'email'


class TestDictConversion:
    """Test dictionary key conversion"""
    
    def test_simple_dict_to_camel(self):
        input_dict = {
            'user_id': '123',
            'created_at': '2024-01-15',
            'updated_at': '2024-01-16'
        }
        expected = {
            'userId': '123',
            'createdAt': '2024-01-15',
            'updatedAt': '2024-01-16'
        }
        assert convert_dict_keys_to_camel(input_dict) == expected
    
    def test_nested_dict_to_camel(self):
        input_dict = {
            'user': {
                'user_id': '123',
                'created_at': '2024',
                'group_ids': ['g1', 'g2']
            }
        }
        expected = {
            'user': {
                'userId': '123',
                'createdAt': '2024',
                'groupIds': ['g1', 'g2']
            }
        }
        assert convert_dict_keys_to_camel(input_dict) == expected
    
    def test_list_of_dicts_to_camel(self):
        input_list = [
            {'user_id': '1', 'created_at': '2024'},
            {'user_id': '2', 'created_at': '2024'}
        ]
        expected = [
            {'userId': '1', 'createdAt': '2024'},
            {'userId': '2', 'createdAt': '2024'}
        ]
        assert convert_dict_keys_to_camel(input_list) == expected
    
    def test_simple_dict_to_snake(self):
        input_dict = {
            'userId': '123',
            'createdAt': '2024-01-15',
            'updatedAt': '2024-01-16'
        }
        expected = {
            'user_id': '123',
            'created_at': '2024-01-15',
            'updated_at': '2024-01-16'
        }
        assert convert_dict_keys_to_snake(input_dict) == expected


class TestRealWorldExamples:
    """Test with real API response examples"""
    
    def test_user_response(self):
        """Test user response conversion"""
        backend_response = {
            'user': {
                'id': 'user-123',
                'name': 'John Doe',
                'email': 'john@example.com',
                'role': 'user',
                'status': 'active',
                'created_at': '2024-01-15T10:30:00Z',
                'updated_at': '2024-01-15T12:00:00Z',
                'group_ids': ['group-1', 'group-2']
            }
        }
        
        frontend_expected = {
            'user': {
                'id': 'user-123',
                'name': 'John Doe',
                'email': 'john@example.com',
                'role': 'user',
                'status': 'active',
                'createdAt': '2024-01-15T10:30:00Z',
                'updatedAt': '2024-01-15T12:00:00Z',
                'groupIds': ['group-1', 'group-2']
            }
        }
        
        assert convert_dict_keys_to_camel(backend_response) == frontend_expected
    
    def test_conversation_response(self):
        """Test conversation response conversion"""
        backend_response = {
            'conversation': {
                'id': 'conv-123',
                'title': 'My Conversation',
                'owner_id': 'user-456',
                'group_id': 'group-1',
                'shared_with_group_ids': ['group-2', 'group-3'],
                'is_shared': True,
                'message_count': 42,
                'created_at': '2024-01-15T10:30:00Z',
                'updated_at': '2024-01-15T12:00:00Z'
            }
        }
        
        frontend_expected = {
            'conversation': {
                'id': 'conv-123',
                'title': 'My Conversation',
                'ownerId': 'user-456',
                'groupId': 'group-1',
                'sharedWithGroupIds': ['group-2', 'group-3'],
                'isShared': True,
                'messageCount': 42,
                'createdAt': '2024-01-15T10:30:00Z',
                'updatedAt': '2024-01-15T12:00:00Z'
            }
        }
        
        assert convert_dict_keys_to_camel(backend_response) == frontend_expected
    
    def test_message_list_response(self):
        """Test message list response conversion"""
        backend_response = {
            'messages': [
                {
                    'id': 'msg-1',
                    'conversation_id': 'conv-123',
                    'role': 'user',
                    'content': 'Hello',
                    'timestamp': '2024-01-15T10:30:00Z'
                },
                {
                    'id': 'msg-2',
                    'conversation_id': 'conv-123',
                    'role': 'assistant',
                    'content': 'Hi there!',
                    'timestamp': '2024-01-15T10:31:00Z'
                }
            ]
        }
        
        frontend_expected = {
            'messages': [
                {
                    'id': 'msg-1',
                    'conversationId': 'conv-123',
                    'role': 'user',
                    'content': 'Hello',
                    'timestamp': '2024-01-15T10:30:00Z'
                },
                {
                    'id': 'msg-2',
                    'conversationId': 'conv-123',
                    'role': 'assistant',
                    'content': 'Hi there!',
                    'timestamp': '2024-01-15T10:31:00Z'
                }
            ]
        }
        
        assert convert_dict_keys_to_camel(backend_response) == frontend_expected
    
    def test_file_response(self):
        """Test file response conversion"""
        backend_response = {
            'file': {
                'id': 'file-123',
                'name': 'document.pdf',
                'size': 1024000,
                'type': 'application/pdf',
                'url': 'https://storage.example.com/file-123',
                'uploaded_at': '2024-01-15T10:30:00Z',
                'uploaded_by': 'user-456'
            }
        }
        
        frontend_expected = {
            'file': {
                'id': 'file-123',
                'name': 'document.pdf',
                'size': 1024000,
                'type': 'application/pdf',
                'url': 'https://storage.example.com/file-123',
                'uploadedAt': '2024-01-15T10:30:00Z',
                'uploadedBy': 'user-456'
            }
        }
        
        assert convert_dict_keys_to_camel(backend_response) == frontend_expected


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
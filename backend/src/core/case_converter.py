"""
Path: backend/src/core/case_converter.py
Version: 1

Automatic snake_case to camelCase converter for API responses
Preserves existing code, converts only at serialization/deserialization
"""

import re
from typing import Any, Dict, List, Union


def snake_to_camel(snake_str: str) -> str:
    """
    Convert snake_case to camelCase
    
    Args:
        snake_str: String in snake_case format
        
    Returns:
        String in camelCase format
        
    Examples:
        >>> snake_to_camel('user_id')
        'userId'
        >>> snake_to_camel('created_at')
        'createdAt'
        >>> snake_to_camel('shared_with_group_ids')
        'sharedWithGroupIds'
    """
    components = snake_str.split('_')
    # Keep first component as-is, capitalize the rest
    return components[0] + ''.join(x.title() for x in components[1:])


def camel_to_snake(camel_str: str) -> str:
    """
    Convert camelCase to snake_case
    
    Args:
        camel_str: String in camelCase format
        
    Returns:
        String in snake_case format
        
    Examples:
        >>> camel_to_snake('userId')
        'user_id'
        >>> camel_to_snake('createdAt')
        'created_at'
        >>> camel_to_snake('sharedWithGroups')
        'shared_with_groups'
    """
    # Insert underscore before uppercase letters and convert to lowercase
    snake_str = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', snake_str).lower()


def convert_dict_keys_to_camel(data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    """
    Recursively convert all dictionary keys from snake_case to camelCase
    
    Args:
        data: Dictionary, list, or other data structure
        
    Returns:
        Same structure with camelCase keys
        
    Examples:
        >>> convert_dict_keys_to_camel({'user_id': '123', 'created_at': '2024'})
        {'userId': '123', 'createdAt': '2024'}
    """
    if isinstance(data, dict):
        return {
            snake_to_camel(key): convert_dict_keys_to_camel(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [convert_dict_keys_to_camel(item) for item in data]
    else:
        return data


def convert_dict_keys_to_snake(data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    """
    Recursively convert all dictionary keys from camelCase to snake_case
    
    Args:
        data: Dictionary, list, or other data structure
        
    Returns:
        Same structure with snake_case keys
        
    Examples:
        >>> convert_dict_keys_to_snake({'userId': '123', 'createdAt': '2024'})
        {'user_id': '123', 'created_at': '2024'}
    """
    if isinstance(data, dict):
        return {
            camel_to_snake(key): convert_dict_keys_to_snake(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [convert_dict_keys_to_snake(item) for item in data]
    else:
        return data


# Convenience functions for common patterns
def response_to_camel(response_dict: Dict) -> Dict:
    """
    Convert API response from snake_case to camelCase
    
    Use this in endpoints before returning response
    
    Args:
        response_dict: Response dictionary with snake_case keys
        
    Returns:
        Response dictionary with camelCase keys
    """
    return convert_dict_keys_to_camel(response_dict)


def request_to_snake(request_dict: Dict) -> Dict:
    """
    Convert API request from camelCase to snake_case
    
    Use this in endpoints to parse incoming request
    
    Args:
        request_dict: Request dictionary with camelCase keys
        
    Returns:
        Request dictionary with snake_case keys
    """
    return convert_dict_keys_to_snake(request_dict)
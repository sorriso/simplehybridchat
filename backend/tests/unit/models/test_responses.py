"""
Path: backend/tests/unit/models/test_responses.py
Version: 1

Unit tests for API response wrappers
"""

import pytest
from src.models.responses import (
    SuccessResponse,
    ErrorResponse,
    PaginatedResponse,
    EmptyResponse
)


class TestSuccessResponse:
    """Test SuccessResponse wrapper"""
    
    @pytest.mark.unit
    def test_success_response_with_data(self):
        """Test success response with data"""
        response = SuccessResponse(
            data={"id": "123", "name": "John"},
            message="User created"
        )
        
        assert response.success is True
        assert response.data == {"id": "123", "name": "John"}
        assert response.message == "User created"
    
    @pytest.mark.unit
    def test_success_response_without_message(self):
        """Test success response without message"""
        response = SuccessResponse(data={"id": "123"})
        
        assert response.success is True
        assert response.data == {"id": "123"}
        assert response.message is None
    
    @pytest.mark.unit
    def test_success_response_with_list(self):
        """Test success response with list data"""
        response = SuccessResponse(
            data=[{"id": "1"}, {"id": "2"}]
        )
        
        assert response.success is True
        assert len(response.data) == 2
    
    @pytest.mark.unit
    def test_success_response_json_serialization(self):
        """Test JSON serialization"""
        response = SuccessResponse(data={"id": "123"})
        json_data = response.model_dump()
        
        assert json_data["success"] is True
        assert json_data["data"] == {"id": "123"}


class TestErrorResponse:
    """Test ErrorResponse wrapper"""
    
    @pytest.mark.unit
    def test_error_response_basic(self):
        """Test basic error response"""
        response = ErrorResponse(
            error="User not found",
            code="NOT_FOUND"
        )
        
        assert response.success is False
        assert response.error == "User not found"
        assert response.code == "NOT_FOUND"
        assert response.details is None
    
    @pytest.mark.unit
    def test_error_response_with_details(self):
        """Test error response with details"""
        response = ErrorResponse(
            error="Validation failed",
            code="VALIDATION_ERROR",
            details={"field": "email", "issue": "invalid format"}
        )
        
        assert response.success is False
        assert response.error == "Validation failed"
        assert response.details["field"] == "email"
    
    @pytest.mark.unit
    def test_error_response_without_code(self):
        """Test error response without code"""
        response = ErrorResponse(error="Something went wrong")
        
        assert response.success is False
        assert response.error == "Something went wrong"
        assert response.code is None


class TestPaginatedResponse:
    """Test PaginatedResponse wrapper"""
    
    @pytest.mark.unit
    def test_paginated_response_create(self):
        """Test creating paginated response"""
        data = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
        response = PaginatedResponse.create(
            data=data,
            total=100,
            page=1,
            per_page=10
        )
        
        assert response.success is True
        assert len(response.data) == 3
        assert response.pagination["total"] == 100
        assert response.pagination["page"] == 1
        assert response.pagination["per_page"] == 10
        assert response.pagination["pages"] == 10
        assert response.pagination["has_next"] is True
        assert response.pagination["has_prev"] is False
    
    @pytest.mark.unit
    def test_paginated_response_last_page(self):
        """Test last page pagination"""
        response = PaginatedResponse.create(
            data=[{"id": "1"}],
            total=25,
            page=3,
            per_page=10
        )
        
        assert response.pagination["pages"] == 3
        assert response.pagination["has_next"] is False
        assert response.pagination["has_prev"] is True
    
    @pytest.mark.unit
    def test_paginated_response_middle_page(self):
        """Test middle page pagination"""
        response = PaginatedResponse.create(
            data=[],
            total=100,
            page=5,
            per_page=10
        )
        
        assert response.pagination["has_next"] is True
        assert response.pagination["has_prev"] is True
    
    @pytest.mark.unit
    def test_paginated_response_empty(self):
        """Test paginated response with no data"""
        response = PaginatedResponse.create(
            data=[],
            total=0,
            page=1,
            per_page=10
        )
        
        assert response.success is True
        assert len(response.data) == 0
        assert response.pagination["total"] == 0
        assert response.pagination["pages"] == 0
    
    @pytest.mark.unit
    def test_paginated_response_calculation(self):
        """Test page calculation edge cases"""
        # Exact fit
        response = PaginatedResponse.create(
            data=[],
            total=30,
            page=1,
            per_page=10
        )
        assert response.pagination["pages"] == 3
        
        # One extra
        response = PaginatedResponse.create(
            data=[],
            total=31,
            page=1,
            per_page=10
        )
        assert response.pagination["pages"] == 4


class TestEmptyResponse:
    """Test EmptyResponse wrapper"""
    
    @pytest.mark.unit
    def test_empty_response_with_message(self):
        """Test empty response with message"""
        response = EmptyResponse(message="User deleted")
        
        assert response.success is True
        assert response.message == "User deleted"
    
    @pytest.mark.unit
    def test_empty_response_without_message(self):
        """Test empty response without message"""
        response = EmptyResponse()
        
        assert response.success is True
        assert response.message is None
    
    @pytest.mark.unit
    def test_empty_response_json_serialization(self):
        """Test JSON serialization"""
        response = EmptyResponse(message="Operation complete")
        json_data = response.model_dump()
        
        assert json_data["success"] is True
        assert json_data["message"] == "Operation complete"
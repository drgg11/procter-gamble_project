import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from pg_fastapi import app, get_db, IdentifiersCreate
from main import Identifiers, Base
from connectdb import engine


# Test client setup
client = TestClient(app)


@pytest.fixture(scope="function")
def setup_and_teardown_db():
    """Create tables before tests and drop them after"""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


class TestRoot:
    """Test root endpoint"""
    
    def test_root(self):
        response = client.get('/')
        assert response.status_code == 200
        assert response.json() == {'message': 'Procter & Gamble Database API'}


class TestCreateIdentifier:
    """Test creating identifiers"""
    
    def test_create_identifier_success(self, setup_and_teardown_db):
        payload = {
            "identifier_name": "TEST_ID_001",
            "description": "Test identifier",
            "identifier_type": "Product"
        }
        response = client.post("/identifiers/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["identifier_name"] == "TEST_ID_001"
        assert data["description"] == "Test identifier"
        assert data["identifier_type"] == "Product"
    
    def test_create_identifier_minimal(self, setup_and_teardown_db):
        payload = {"identifier_name": "TEST_ID_002"}
        response = client.post("/identifiers/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["identifier_name"] == "TEST_ID_002"
        assert data["description"] is None


class TestReadIdentifiers:
    """Test reading identifiers"""
    
    def test_read_all_identifiers_empty(self, setup_and_teardown_db):
        response = client.get("/identifiers/")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_read_all_identifiers_multiple(self, setup_and_teardown_db):
        # Create multiple identifiers
        identifiers_data = [
            {"identifier_name": "ID_001", "description": "First", "identifier_type": "Type1"},
            {"identifier_name": "ID_002", "description": "Second", "identifier_type": "Type2"},
            {"identifier_name": "ID_003", "description": "Third", "identifier_type": "Type3"},
        ]
        
        for payload in identifiers_data:
            client.post("/identifiers/", json=payload)
        
        response = client.get("/identifiers/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["identifier_name"] == "ID_001"
    
    def test_read_single_identifier_success(self, setup_and_teardown_db):
        # Create identifier first
        payload = {
            "identifier_name": "READ_TEST_ID",
            "description": "Read test",
            "identifier_type": "Test"
        }
        client.post("/identifiers/", json=payload)
        
        # Read it back
        response = client.get("/identifiers/READ_TEST_ID")
        assert response.status_code == 200
        data = response.json()
        assert data["identifier_name"] == "READ_TEST_ID"
        assert data["description"] == "Read test"
    
    def test_read_single_identifier_not_found(self, setup_and_teardown_db):
        response = client.get("/identifiers/NONEXISTENT_ID")
        assert response.status_code == 404
        assert response.json()["detail"] == "Identifier not found"


class TestUpdateIdentifier:
    """Test updating identifiers"""
    
    def test_update_identifier_success(self, setup_and_teardown_db):
        # Create identifier
        create_payload = {
            "identifier_name": "UPDATE_TEST_ID",
            "description": "Original",
            "identifier_type": "Original"
        }
        client.post("/identifiers/", json=create_payload)
        
        # Update it
        update_payload = {
            "identifier_name": "UPDATE_TEST_ID",
            "description": "Updated",
            "identifier_type": "UpdatedType"
        }
        response = client.put("/identifiers/UPDATE_TEST_ID", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated"
        assert data["identifier_type"] == "UpdatedType"
    
    def test_update_identifier_not_found(self, setup_and_teardown_db):
        payload = {
            "identifier_name": "NONEXISTENT",
            "description": "Test",
            "identifier_type": "Test"
        }
        response = client.put("/identifiers/NONEXISTENT", json=payload)
        assert response.status_code == 404


class TestPatchIdentifier:
    """Test partial updates to identifiers"""
    
    def test_patch_identifier_description_only(self, setup_and_teardown_db):
        # Create identifier
        create_payload = {
            "identifier_name": "PATCH_TEST_ID",
            "description": "Original",
            "identifier_type": "Original"
        }
        client.post("/identifiers/", json=create_payload)
        
        # Patch only description
        patch_payload = {
            "identifier_name": "PATCH_TEST_ID",
            "description": "Patched Description"
        }
        response = client.patch("/identifiers/PATCH_TEST_ID", json=patch_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Patched Description"
        assert data["identifier_type"] == "Original"  # Unchanged
    
    def test_patch_identifier_type_only(self, setup_and_teardown_db):
        # Create identifier
        create_payload = {
            "identifier_name": "PATCH_TEST_ID_2",
            "description": "Original",
            "identifier_type": "Original"
        }
        client.post("/identifiers/", json=create_payload)
        
        # Patch only type
        patch_payload = {
            "identifier_name": "PATCH_TEST_ID_2",
            "identifier_type": "Patched Type"
        }
        response = client.patch("/identifiers/PATCH_TEST_ID_2", json=patch_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Original"  # Unchanged
        assert data["identifier_type"] == "Patched Type"
    
    def test_patch_identifier_not_found(self, setup_and_teardown_db):
        patch_payload = {
            "identifier_name": "NONEXISTENT_PATCH",
            "description": "Test"
        }
        response = client.patch("/identifiers/NONEXISTENT_PATCH", json=patch_payload)
        assert response.status_code == 404


class TestDeleteIdentifier:
    """Test deleting identifiers"""
    
    def test_delete_identifier_success(self, setup_and_teardown_db):
        # Create identifier
        create_payload = {
            "identifier_name": "DELETE_TEST_ID",
            "description": "To be deleted",
            "identifier_type": "Delete"
        }
        client.post("/identifiers/", json=create_payload)
        
        # Verify it exists
        response = client.get("/identifiers/DELETE_TEST_ID")
        assert response.status_code == 200
        
        # Delete it
        response = client.delete("/identifiers/DELETE_TEST_ID")
        assert response.status_code == 200
        assert response.json()["detail"] == "Identifier deleted"
        
        # Verify it's gone
        response = client.get("/identifiers/DELETE_TEST_ID")
        assert response.status_code == 404
    
    def test_delete_identifier_not_found(self, setup_and_teardown_db):
        response = client.delete("/identifiers/NONEXISTENT_DELETE")
        assert response.status_code == 404


class TestIntegrationFlow:
    """Test complete workflows"""
    
    def test_full_crud_workflow(self, setup_and_teardown_db):
        # Create
        create_payload = {
            "identifier_name": "WORKFLOW_ID",
            "description": "Workflow test",
            "identifier_type": "WorkflowType"
        }
        response = client.post("/identifiers/", json=create_payload)
        assert response.status_code == 200
        
        # Read
        response = client.get("/identifiers/WORKFLOW_ID")
        assert response.status_code == 200
        
        # Update
        update_payload = {
            "identifier_name": "WORKFLOW_ID",
            "description": "Updated",
            "identifier_type": "UpdatedType"
        }
        response = client.put("/identifiers/WORKFLOW_ID", json=update_payload)
        assert response.status_code == 200
        
        # Patch
        patch_payload = {
            "identifier_name": "WORKFLOW_ID",
            "description": "Patched"
        }
        response = client.patch("/identifiers/WORKFLOW_ID", json=patch_payload)
        assert response.status_code == 200
        
        # Delete
        response = client.delete("/identifiers/WORKFLOW_ID")
        assert response.status_code == 200
        
        # Verify deletion
        response = client.get("/identifiers/WORKFLOW_ID")
        assert response.status_code == 404

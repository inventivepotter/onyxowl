"""
Tests for FastAPI endpoints
Run with: pytest tests/test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient

# Import with PYTHONPATH handling
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from main import app


@pytest.fixture
def client():
    """Create test client with proper state initialization"""
    # Initialize app state for testing (mimics lifespan without NATS)
    app.state.use_nats = False
    return TestClient(app)


class TestMaskEndpoint:
    """Tests for /mask endpoint"""

    def test_mask_basic(self, client):
        """Test basic masking"""
        response = client.post(
            "/mask",
            json={"text": "Email me at john@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "masked_text" in data
        assert "session_id" in data
        assert "{{__OWL:EMAIL_ADDRESS_1__}}" in data["masked_text"]
        assert "john@example.com" not in data["masked_text"]

    def test_mask_with_custom_session_id(self, client):
        """Test masking with custom session_id"""
        custom_id = "my-custom-session-123"
        response = client.post(
            "/mask",
            json={
                "text": "Email me at john@example.com",
                "session_id": custom_id
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == custom_id

    def test_mask_auto_generated_session_id(self, client):
        """Test that session_id is auto-generated when not provided"""
        response = client.post(
            "/mask",
            json={"text": "Email me at john@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        # UUID format: 8-4-4-4-12 = 36 chars
        assert len(data["session_id"]) == 36
        assert "-" in data["session_id"]

    def test_mask_with_selective_entities(self, client):
        """Test masking specific entity types"""
        response = client.post(
            "/mask",
            json={
                "text": "Email john@example.com, Phone (555) 123-4567",
                "entities_to_mask": ["EMAIL_ADDRESS"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "john@example.com" not in data["masked_text"]

    def test_mask_with_custom_session_and_selective_entities(self, client):
        """Test custom session_id with selective masking"""
        custom_id = "selective-session-456"
        response = client.post(
            "/mask",
            json={
                "text": "Email john@example.com",
                "entities_to_mask": ["EMAIL_ADDRESS"],
                "session_id": custom_id
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == custom_id
        assert "john@example.com" not in data["masked_text"]

    def test_mask_empty_text(self, client):
        """Test masking empty text"""
        response = client.post(
            "/mask",
            json={"text": ""}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["masked_text"] == ""
        assert data["entities_found"] == 0

    def test_mask_no_pii(self, client):
        """Test text without PII"""
        text = "Hello world, this has no sensitive data"
        response = client.post(
            "/mask",
            json={"text": text}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["masked_text"] == text
        assert data["entities_found"] == 0


class TestDemaskEndpoint:
    """Tests for /demask endpoint"""

    def test_demask_basic(self, client):
        """Test basic demasking"""
        # First mask
        mask_response = client.post(
            "/mask",
            json={"text": "Email me at john@example.com"}
        )
        mask_data = mask_response.json()

        # Then demask
        demask_response = client.post(
            "/demask",
            json={
                "masked_text": mask_data["masked_text"],
                "session_id": mask_data["session_id"]
            }
        )
        assert demask_response.status_code == 200
        demask_data = demask_response.json()
        assert "john@example.com" in demask_data["original_text"]

    def test_demask_with_custom_session_id(self, client):
        """Test demasking with custom session_id"""
        custom_id = "demask-test-session"

        # Mask with custom session_id
        mask_response = client.post(
            "/mask",
            json={
                "text": "Email me at alice@company.com",
                "session_id": custom_id
            }
        )
        mask_data = mask_response.json()
        assert mask_data["session_id"] == custom_id

        # Demask using same session_id
        demask_response = client.post(
            "/demask",
            json={
                "masked_text": mask_data["masked_text"],
                "session_id": custom_id
            }
        )
        assert demask_response.status_code == 200
        demask_data = demask_response.json()
        assert "alice@company.com" in demask_data["original_text"]


class TestResolveEndpoint:
    """Tests for /resolve endpoint"""

    def test_resolve_tokens(self, client):
        """Test resolving specific tokens"""
        # First mask
        mask_response = client.post(
            "/mask",
            json={"text": "Email john@example.com and call (555) 123-4567"}
        )
        mask_data = mask_response.json()

        # Get tokens from token_map
        tokens = list(mask_data["token_map"].keys())

        # Resolve tokens
        resolve_response = client.post(
            "/resolve",
            json={
                "session_id": mask_data["session_id"],
                "tokens": tokens
            }
        )
        assert resolve_response.status_code == 200
        resolve_data = resolve_response.json()
        assert "resolved" in resolve_data
        assert len(resolve_data["resolved"]) == len(tokens)

    def test_resolve_with_custom_session_id(self, client):
        """Test resolving tokens with custom session_id"""
        custom_id = "resolve-test-session"

        # Mask with custom session_id
        mask_response = client.post(
            "/mask",
            json={
                "text": "Email john@example.com",
                "session_id": custom_id
            }
        )
        mask_data = mask_response.json()

        # Resolve using custom session_id
        resolve_response = client.post(
            "/resolve",
            json={
                "session_id": custom_id,
                "tokens": ["{{__OWL:EMAIL_ADDRESS_1__}}"]
            }
        )
        assert resolve_response.status_code == 200
        resolve_data = resolve_response.json()
        assert "john@example.com" in resolve_data["resolved"].values()


class TestLLMFlowEndpoint:
    """Tests for /llm-flow endpoint"""

    def test_llm_flow_mask_step(self, client):
        """Test LLM flow - mask step"""
        response = client.post(
            "/llm-flow",
            json={"user_input": "My email is alice@company.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "masked_input" in data
        assert "session_id" in data
        assert "{{__OWL:EMAIL_ADDRESS_1__}}" in data["masked_input"]

    def test_llm_flow_demask_step(self, client):
        """Test LLM flow - demask step"""
        # Step 1: Mask
        mask_response = client.post(
            "/llm-flow",
            json={"user_input": "My email is alice@company.com"}
        )
        mask_data = mask_response.json()

        # Step 2: Demask (simulating LLM response)
        demask_response = client.post(
            "/llm-flow",
            json={
                "user_input": "",
                "llm_response": "I'll email {{__OWL:EMAIL_ADDRESS_1__}}",
                "session_id": mask_data["session_id"]
            }
        )
        assert demask_response.status_code == 200
        demask_data = demask_response.json()
        assert "alice@company.com" in demask_data["demasked_response"]


class TestSessionEndpoint:
    """Tests for session management endpoint"""

    def test_clear_session(self, client):
        """Test clearing session"""
        # First mask to create session
        mask_response = client.post(
            "/mask",
            json={"text": "Email john@example.com"}
        )
        session_id = mask_response.json()["session_id"]

        # Clear session
        clear_response = client.delete(f"/session/{session_id}")
        assert clear_response.status_code == 200
        data = clear_response.json()
        assert data["status"] == "cleared"
        assert data["session_id"] == session_id

    def test_clear_custom_session(self, client):
        """Test clearing custom session_id"""
        custom_id = "clear-test-session"

        # Mask with custom session_id
        client.post(
            "/mask",
            json={
                "text": "Email john@example.com",
                "session_id": custom_id
            }
        )

        # Clear session
        clear_response = client.delete(f"/session/{custom_id}")
        assert clear_response.status_code == 200
        data = clear_response.json()
        assert data["session_id"] == custom_id


class TestHealthEndpoint:
    """Tests for health check endpoint"""

    def test_health_check(self, client):
        """Test health check returns expected fields"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "gliner_enabled" in data
        assert "active_sessions" in data
        assert "nats_enabled" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

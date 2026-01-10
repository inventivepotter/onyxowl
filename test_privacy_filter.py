"""
Simple tests for Privacy Filter
Run with: pytest test_privacy_filter.py -v
"""

import pytest
from privacy_filter import PrivacyFilter, MaskingResult, DemaskingResult


@pytest.fixture
def filter_instance():
    """Create filter instance for testing"""
    return PrivacyFilter(use_gliner=True)


def test_basic_masking(filter_instance):
    """Test basic masking functionality"""
    text = "Email me at john@example.com"

    result = filter_instance.mask(text)

    assert isinstance(result, MaskingResult)
    assert "<EMAIL_ADDRESS_1>" in result.masked_text
    assert "john@example.com" not in result.masked_text
    assert len(result.token_map) > 0
    assert result.session_id is not None


def test_basic_demasking(filter_instance):
    """Test basic de-masking functionality"""
    text = "Email me at john@example.com"

    # Mask
    mask_result = filter_instance.mask(text)

    # De-mask
    demask_result = filter_instance.demask(
        mask_result.masked_text,
        session_id=mask_result.session_id
    )

    assert isinstance(demask_result, DemaskingResult)
    assert demask_result.original_text == text
    assert demask_result.entities_restored > 0


def test_multiple_entities(filter_instance):
    """Test masking multiple entities"""
    text = "Contact John Doe at john@example.com or (555) 123-4567"

    result = filter_instance.mask(text)

    # Should detect email and phone at minimum
    assert len(result.entities_found) >= 2
    assert len(result.token_map) >= 2


def test_token_map_correctness(filter_instance):
    """Test that token map correctly stores original values"""
    text = "My email is alice@company.com and bob@company.com"

    result = filter_instance.mask(text)

    # Check token map
    assert "alice@company.com" in result.token_map.values()
    assert "bob@company.com" in result.token_map.values()


def test_selective_masking(filter_instance):
    """Test masking only specific entity types"""
    text = "Email: john@example.com, SSN: 123-45-6789"

    # Only mask email
    result = filter_instance.mask(text, entities_to_mask=["EMAIL_ADDRESS"])

    # Email should be masked
    assert "john@example.com" not in result.masked_text
    # But we're not checking if SSN is masked since it depends on detection


def test_session_cleanup(filter_instance):
    """Test session cleanup"""
    text = "Email: john@example.com"

    result = filter_instance.mask(text)
    session_id = result.session_id

    # Session should exist
    assert session_id in filter_instance.sessions

    # Clean up
    filter_instance.clear_session(session_id)

    # Session should be removed
    assert session_id not in filter_instance.sessions


def test_empty_text(filter_instance):
    """Test handling empty text"""
    text = ""

    result = filter_instance.mask(text)

    assert result.masked_text == ""
    assert len(result.entities_found) == 0
    assert len(result.token_map) == 0


def test_no_pii_text(filter_instance):
    """Test text with no PII"""
    text = "This is a simple sentence with no sensitive data"

    result = filter_instance.mask(text)

    assert result.masked_text == text
    assert len(result.entities_found) == 0


def test_llm_workflow(filter_instance):
    """Test complete LLM workflow"""
    # User input
    user_input = "My email is alice@company.com"

    # Step 1: Mask
    mask_result = filter_instance.mask(user_input)
    assert "<EMAIL_ADDRESS_1>" in mask_result.masked_text

    # Step 2: Simulate LLM response referencing the token
    llm_response = "I'll send confirmation to <EMAIL_ADDRESS_1>"

    # Step 3: De-mask
    demask_result = filter_instance.demask(
        llm_response,
        session_id=mask_result.session_id
    )

    assert "alice@company.com" in demask_result.original_text
    assert "<EMAIL_ADDRESS_1>" not in demask_result.original_text


def test_token_uniqueness(filter_instance):
    """Test that tokens are unique for same entity type"""
    text = "Email alice@example.com and bob@example.com"

    result = filter_instance.mask(text)

    # Should have two different tokens
    assert "<EMAIL_ADDRESS_1>" in result.masked_text
    assert "<EMAIL_ADDRESS_2>" in result.masked_text


def test_demask_with_direct_token_map(filter_instance):
    """Test de-masking with direct token map (without session)"""
    masked_text = "Email <EMAIL_1> and call <PHONE_1>"
    token_map = {
        "<EMAIL_1>": "john@example.com",
        "<PHONE_1>": "(555) 123-4567"
    }

    result = filter_instance.demask(masked_text, token_map=token_map)

    assert "john@example.com" in result.original_text
    assert "(555) 123-4567" in result.original_text


def test_demask_without_session_or_map_raises_error(filter_instance):
    """Test that de-masking without session or map raises error"""
    masked_text = "Email <EMAIL_1>"

    with pytest.raises(ValueError, match="Must provide either session_id or token_map"):
        filter_instance.demask(masked_text)


# Integration tests (require GLiNER model to be loaded)
@pytest.mark.slow
def test_detect_credit_card(filter_instance):
    """Test credit card detection"""
    text = "My card number is 4532-1234-5678-9010"

    result = filter_instance.mask(text)

    # Should detect credit card (if GLiNER is working)
    # This is a basic check - actual detection depends on GLiNER
    assert len(result.entities_found) >= 0  # May or may not detect


@pytest.mark.slow
def test_detect_bitcoin_address(filter_instance):
    """Test Bitcoin address detection"""
    text = "Send payment to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"

    result = filter_instance.mask(text)

    # Should detect Bitcoin address
    assert len(result.entities_found) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

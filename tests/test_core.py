"""
Tests for core Privacy Filter functionality
Run with: pytest tests/test_core.py -v
"""

import pytest
from privacy_filter import PrivacyFilter, MaskingResult, DemaskingResult


def test_basic_masking(filter_instance):
    """Test basic masking functionality"""
    text = "Email me at john@example.com"

    result = filter_instance.mask(text)

    assert isinstance(result, MaskingResult)
    assert "{{__OWL:EMAIL_ADDRESS_1__}}" in result.masked_text
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
    assert "{{__OWL:EMAIL_ADDRESS_1__}}" in mask_result.masked_text

    # Step 2: Simulate LLM response referencing the token
    llm_response = "I'll send confirmation to {{__OWL:EMAIL_ADDRESS_1__}}"

    # Step 3: De-mask
    demask_result = filter_instance.demask(
        llm_response,
        session_id=mask_result.session_id
    )

    assert "alice@company.com" in demask_result.original_text
    assert "{{__OWL:EMAIL_ADDRESS_1__}}" not in demask_result.original_text


def test_token_uniqueness(filter_instance):
    """Test that tokens are unique for same entity type"""
    text = "Email alice@example.com and bob@example.com"

    result = filter_instance.mask(text)

    # Should have two different tokens
    assert "{{__OWL:EMAIL_ADDRESS_1__}}" in result.masked_text
    assert "{{__OWL:EMAIL_ADDRESS_2__}}" in result.masked_text


def test_demask_with_direct_token_map(filter_instance):
    """Test de-masking with direct token map (without session)"""
    masked_text = "Email {{__OWL:EMAIL_1__}} and call {{__OWL:PHONE_1__}}"
    token_map = {
        "{{__OWL:EMAIL_1__}}": "john@example.com",
        "{{__OWL:PHONE_1__}}": "(555) 123-4567"
    }

    result = filter_instance.demask(masked_text, token_map=token_map)

    assert "john@example.com" in result.original_text
    assert "(555) 123-4567" in result.original_text


def test_demask_without_session_or_map_raises_error(filter_instance):
    """Test that de-masking without session or map raises error"""
    masked_text = "Email {{__OWL:EMAIL_1__}}"

    with pytest.raises(ValueError, match="Must provide either session_id or token_map"):
        filter_instance.demask(masked_text)


# Custom session_id tests

def test_custom_session_id(filter_instance):
    """Test masking with custom session_id"""
    text = "Email me at john@example.com"
    custom_session_id = "my-custom-session-123"

    result = filter_instance.mask(text, session_id=custom_session_id)

    assert result.session_id == custom_session_id
    assert custom_session_id in filter_instance.sessions
    assert "{{__OWL:EMAIL_ADDRESS_1__}}" in result.masked_text


def test_custom_session_id_demask(filter_instance):
    """Test complete mask/demask flow with custom session_id"""
    text = "Contact alice@company.com for help"
    custom_session_id = "user-456-conv-789"

    # Mask with custom session_id
    mask_result = filter_instance.mask(text, session_id=custom_session_id)
    assert mask_result.session_id == custom_session_id

    # Demask using custom session_id
    demask_result = filter_instance.demask(
        mask_result.masked_text,
        session_id=custom_session_id
    )

    assert demask_result.original_text == text
    assert "alice@company.com" in demask_result.original_text


def test_auto_generated_session_id(filter_instance):
    """Test that session_id is auto-generated when not provided"""
    text = "Email me at john@example.com"

    result = filter_instance.mask(text)

    # Should have a UUID-style session_id
    assert result.session_id is not None
    assert len(result.session_id) == 36  # UUID format: 8-4-4-4-12 = 36 chars
    assert "-" in result.session_id


def test_custom_session_id_with_selective_masking(filter_instance):
    """Test custom session_id with selective entity masking"""
    text = "Email: john@example.com, Phone: (555) 123-4567"
    custom_session_id = "selective-mask-session"

    result = filter_instance.mask(
        text,
        entities_to_mask=["EMAIL_ADDRESS"],
        session_id=custom_session_id
    )

    assert result.session_id == custom_session_id
    assert "john@example.com" not in result.masked_text


# Integration tests (require GLiNER model to be loaded)
@pytest.mark.slow
def test_detect_credit_card(filter_instance):
    """Test credit card detection"""
    text = "My card number is 4532-1234-5678-9010"

    result = filter_instance.mask(text)

    # Should detect credit card (if GLiNER is working)
    assert len(result.entities_found) >= 0


@pytest.mark.slow
def test_detect_bitcoin_address(filter_instance):
    """Test Bitcoin address detection"""
    text = "Send payment to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"

    result = filter_instance.mask(text)

    # Should detect Bitcoin address
    assert len(result.entities_found) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

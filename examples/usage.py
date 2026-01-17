"""
Example usage of Privacy Filter
"""

from privacy_filter import PrivacyFilter
import json


def example_basic_usage():
    """Basic masking and de-masking example"""
    print("=" * 60)
    print("EXAMPLE 1: Basic Masking and De-masking")
    print("=" * 60)

    # Initialize filter
    filter_instance = PrivacyFilter(use_gliner=True)

    # Original text with PII
    original_text = """
    Hi, my name is John Doe. You can reach me at john.doe@email.com
    or call me at (555) 123-4567. My SSN is 123-45-6789.
    Please send payment to my Bitcoin address: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
    """

    print(f"\nOriginal Text:\n{original_text}")

    # Mask the text
    mask_result = filter_instance.mask(original_text)

    print(f"\nMasked Text:\n{mask_result.masked_text}")
    print(f"\nSession ID: {mask_result.session_id}")
    print(f"\nEntities Found: {len(mask_result.entities_found)}")
    print(f"\nToken Map:")
    for token, value in mask_result.token_map.items():
        print(f"  {token} -> {value}")

    # De-mask the text
    demask_result = filter_instance.demask(
        mask_result.masked_text,
        session_id=mask_result.session_id
    )

    print(f"\nDe-masked Text:\n{demask_result.original_text}")
    print(f"Entities Restored: {demask_result.entities_restored}")


def example_llm_workflow():
    """Complete LLM workflow example"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: LLM Workflow (Mask -> LLM -> De-mask)")
    print("=" * 60)

    filter_instance = PrivacyFilter(use_gliner=True)

    # Step 1: User input with PII
    user_input = """
    I need help with my account. My email is alice@company.com
    and my credit card ending in 4242 was charged twice.
    """

    print(f"\n[User Input with PII]:\n{user_input}")

    # Step 2: Mask before sending to LLM
    mask_result = filter_instance.mask(user_input)
    masked_input = mask_result.masked_text
    session_id = mask_result.session_id

    print(f"\n[Masked Input for LLM]:\n{masked_input}")
    print(f"\nSession ID: {session_id}")

    # Step 3: Simulate LLM response (LLM might reference the masked tokens)
    llm_response = f"""
    I can help you with that! I see the issue with <EMAIL_ADDRESS_1>.
    Let me check the charges on card <CREDIT_CARD_1> for you.
    I'll send you an email confirmation to <EMAIL_ADDRESS_1> shortly.
    """

    print(f"\n[LLM Response with Tokens]:\n{llm_response}")

    # Step 4: De-mask LLM response
    demask_result = filter_instance.demask(
        llm_response,
        session_id=session_id
    )

    print(f"\n[De-masked Response to User]:\n{demask_result.original_text}")

    # Step 5: Clean up session
    filter_instance.clear_session(session_id)
    print(f"\n[Session Cleared]: {session_id}")


def example_selective_masking():
    """Selective masking - only mask specific entity types"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Selective Masking (Only Email and Phone)")
    print("=" * 60)

    filter_instance = PrivacyFilter(use_gliner=True)

    text = """
    Contact John Doe at john@example.com or (555) 123-4567.
    His SSN is 123-45-6789.
    """

    print(f"\nOriginal Text:\n{text}")

    # Only mask email and phone, leave SSN visible
    mask_result = filter_instance.mask(
        text,
        entities_to_mask=["EMAIL_ADDRESS", "PHONE_NUMBER"]
    )

    print(f"\nMasked Text (only email & phone):\n{mask_result.masked_text}")
    print(f"\nToken Map:")
    for token, value in mask_result.token_map.items():
        print(f"  {token} -> {value}")


def example_api_usage():
    """Example API calls (requires running api_endpoint.py)"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: API Usage with cURL")
    print("=" * 60)

    print("""
# Start the API server first:
python api_endpoint.py

# 1. Mask sensitive data
curl -X POST "http://localhost:1001/mask" \\
  -H "Content-Type: application/json" \\
  -d '{
    "text": "Email me at john@example.com or call (555) 123-4567"
  }'

# Response:
# {
#   "masked_text": "Email me at <EMAIL_ADDRESS_1> or call <PHONE_NUMBER_1>",
#   "session_id": "abc-123-def-456",
#   "entities_found": 2,
#   "token_map": {
#     "<EMAIL_ADDRESS_1>": "john@example.com",
#     "<PHONE_NUMBER_1>": "(555) 123-4567"
#   }
# }

# 2. De-mask text
curl -X POST "http://localhost:1001/demask" \\
  -H "Content-Type: application/json" \\
  -d '{
    "masked_text": "Send confirmation to <EMAIL_ADDRESS_1>",
    "session_id": "abc-123-def-456"
  }'

# Response:
# {
#   "original_text": "Send confirmation to john@example.com",
#   "entities_restored": 1
# }

# 3. Complete LLM flow
# Step 1: Mask user input
curl -X POST "http://localhost:1001/llm-flow" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_input": "My email is alice@company.com"
  }'

# Step 2: De-mask LLM response
curl -X POST "http://localhost:1001/llm-flow" \\
  -H "Content-Type: application/json" \\
  -d '{
    "llm_response": "I will send confirmation to <EMAIL_ADDRESS_1>",
    "session_id": "abc-123-def-456"
  }'

# 4. Clear session
curl -X DELETE "http://localhost:1001/session/abc-123-def-456"
    """)


def example_with_python_requests():
    """Example using Python requests library"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Using Python Requests")
    print("=" * 60)

    print("""
import requests

# API base URL
BASE_URL = "http://localhost:1001"

# 1. Mask user input
mask_response = requests.post(
    f"{BASE_URL}/mask",
    json={
        "text": "My email is john@example.com and my card is 4532-1234-5678-9010"
    }
)
mask_data = mask_response.json()
print(f"Masked: {mask_data['masked_text']}")
print(f"Session: {mask_data['session_id']}")

# 2. Send masked text to LLM (your LLM call here)
masked_input = mask_data['masked_text']
session_id = mask_data['session_id']

# Simulate LLM response
llm_response = f"I've updated <EMAIL_ADDRESS_1> and verified <CREDIT_CARD_1>"

# 3. De-mask LLM response
demask_response = requests.post(
    f"{BASE_URL}/demask",
    json={
        "masked_text": llm_response,
        "session_id": session_id
    }
)
demask_data = demask_response.json()
print(f"De-masked: {demask_data['original_text']}")

# 4. Clean up
requests.delete(f"{BASE_URL}/session/{session_id}")
    """)


if __name__ == "__main__":
    print("\n🔒 Privacy Filter Examples\n")

    # Run examples
    example_basic_usage()
    example_llm_workflow()
    example_selective_masking()
    example_api_usage()
    example_with_python_requests()

    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("=" * 60)

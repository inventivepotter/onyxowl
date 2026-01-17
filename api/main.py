"""
FastAPI endpoint for privacy filter with reversible masking.

Supports both in-memory and NATS JetStream session storage.
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from privacy_filter import PrivacyFilter
from privacy_filter.nats_store import NATSSessionStore, get_nats_store

# Check if NATS is enabled
NATS_ENABLED = os.getenv("NATS_URL") is not None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage NATS connection lifecycle."""
    if NATS_ENABLED:
        # Startup: connect to NATS
        store = await get_nats_store()
        app.state.nats_store = store
        app.state.use_nats = True
    else:
        app.state.use_nats = False

    yield

    # Shutdown: disconnect from NATS
    if NATS_ENABLED and hasattr(app.state, "nats_store"):
        await app.state.nats_store.disconnect()


app = FastAPI(
    title="Privacy Filter API",
    description="Mask and de-mask sensitive data using GLiNER + Presidio with NATS session storage",
    version="2.0.0",
    lifespan=lifespan,
)

# Initialize filter instance
filter_instance = PrivacyFilter(use_gliner=True)


# Request/Response Models
class MaskRequest(BaseModel):
    """Request to mask sensitive data"""
    text: str = Field(..., description="Text to mask")
    entities_to_mask: Optional[List[str]] = Field(
        None,
        description="List of entity types to mask (None = all)",
        example=["EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD"]
    )


class MaskResponse(BaseModel):
    """Response with masked text"""
    masked_text: str = Field(..., description="Text with masked entities")
    session_id: str = Field(..., description="Session ID for de-masking")
    entities_found: int = Field(..., description="Number of entities detected")
    token_map: dict = Field(..., description="Mapping of tokens to original values")


class DemaskRequest(BaseModel):
    """Request to restore original text"""
    masked_text: str = Field(..., description="Text with masked tokens")
    session_id: str = Field(..., description="Session ID from masking operation")


class DemaskResponse(BaseModel):
    """Response with restored text"""
    original_text: str = Field(..., description="Restored original text")
    entities_restored: int = Field(..., description="Number of entities restored")


class ResolveRequest(BaseModel):
    """Request to resolve specific tokens"""
    session_id: str = Field(..., description="Session ID from masking operation")
    tokens: List[str] = Field(..., description="List of tokens to resolve")


class ResolveResponse(BaseModel):
    """Response with resolved tokens"""
    resolved: dict = Field(..., description="Mapping of tokens to original values")


class LLMFlowRequest(BaseModel):
    """Complete LLM flow: mask -> LLM -> demask"""
    user_input: str = Field(..., description="User input with PII")
    llm_response: Optional[str] = Field(None, description="LLM response to de-mask")
    session_id: Optional[str] = Field(None, description="Session ID from previous mask")


class LLMFlowResponse(BaseModel):
    """Response for LLM flow"""
    masked_input: str = Field(..., description="Masked user input for LLM")
    session_id: str = Field(..., description="Session ID for de-masking")
    demasked_response: Optional[str] = Field(None, description="De-masked LLM response")


# Dependency to get store
async def get_store() -> Optional[NATSSessionStore]:
    """Get NATS store if available."""
    if app.state.use_nats:
        return await get_nats_store()
    return None


# API Endpoints

@app.post("/mask", response_model=MaskResponse)
async def mask_text(
    request: MaskRequest,
    store: Optional[NATSSessionStore] = Depends(get_store),
):
    """
    Mask sensitive data in text.

    Returns masked text and session ID for de-masking.
    When NATS is enabled, sessions are stored with automatic TTL.
    """
    try:
        result = filter_instance.mask(request.text, request.entities_to_mask)

        # Store in NATS if available
        if store:
            await store.store_session(result.session_id, result.token_map)

        return MaskResponse(
            masked_text=result.masked_text,
            session_id=result.session_id,
            entities_found=len(result.entities_found),
            token_map=result.token_map
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Masking failed: {str(e)}")


@app.post("/demask", response_model=DemaskResponse)
async def demask_text(
    request: DemaskRequest,
    store: Optional[NATSSessionStore] = Depends(get_store),
):
    """
    Restore original text using session ID.

    De-masks tokens using stored token map from masking operation.
    """
    try:
        # Try NATS first, then fall back to in-memory
        token_map = None
        if store:
            token_map = await store.get_session(request.session_id)

        if token_map:
            # Use token map from NATS
            original_text = request.masked_text
            entities_restored = 0
            for masked_token, original_value in token_map.items():
                if masked_token in original_text:
                    original_text = original_text.replace(masked_token, original_value)
                    entities_restored += 1
            return DemaskResponse(
                original_text=original_text,
                entities_restored=entities_restored
            )
        else:
            # Fall back to in-memory storage
            result = filter_instance.demask(
                request.masked_text,
                session_id=request.session_id
            )
            return DemaskResponse(
                original_text=result.original_text,
                entities_restored=result.entities_restored
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"De-masking failed: {str(e)}")


@app.post("/resolve", response_model=ResolveResponse)
async def resolve_tokens(
    request: ResolveRequest,
    store: Optional[NATSSessionStore] = Depends(get_store),
):
    """
    Resolve specific tokens from a session.

    Called by agent frameworks before executing tools to get
    real values for masked tokens in tool arguments.

    Example:
        Request: {"session_id": "abc-123", "tokens": ["<EMAIL_ADDRESS_1>", "<PHONE_NUMBER_1>"]}
        Response: {"resolved": {"<EMAIL_ADDRESS_1>": "john@example.com", "<PHONE_NUMBER_1>": "555-1234"}}
    """
    try:
        if store:
            resolved = await store.resolve_tokens(
                request.session_id,
                request.tokens,
            )
        else:
            # Fall back to in-memory storage
            token_map = filter_instance.sessions.get(request.session_id, {})
            resolved = {
                token: token_map.get(token, token)
                for token in request.tokens
            }

        if not resolved:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {request.session_id}",
            )

        return ResolveResponse(resolved=resolved)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token resolution failed: {str(e)}")


@app.post("/llm-flow", response_model=LLMFlowResponse)
async def llm_flow(
    request: LLMFlowRequest,
    store: Optional[NATSSessionStore] = Depends(get_store),
):
    """
    Complete LLM workflow with privacy protection.

    1. Mask user input -> send to LLM
    2. Receive LLM response -> de-mask and return

    Call this endpoint twice:
    - First call: Only user_input (get masked input + session_id)
    - Second call: llm_response + session_id (get de-masked response)
    """
    try:
        # Step 1: Mask user input (if provided without session_id)
        if request.session_id is None:
            mask_result = filter_instance.mask(request.user_input)

            # Store in NATS if available
            if store:
                await store.store_session(mask_result.session_id, mask_result.token_map)

            return LLMFlowResponse(
                masked_input=mask_result.masked_text,
                session_id=mask_result.session_id,
                demasked_response=None
            )

        # Step 2: De-mask LLM response (if session_id provided)
        if request.llm_response:
            # Try NATS first
            token_map = None
            if store:
                token_map = await store.get_session(request.session_id)

            if token_map:
                original_text = request.llm_response
                for masked_token, original_value in token_map.items():
                    original_text = original_text.replace(masked_token, original_value)
            else:
                demask_result = filter_instance.demask(
                    request.llm_response,
                    session_id=request.session_id
                )
                original_text = demask_result.original_text

            return LLMFlowResponse(
                masked_input="",  # Already processed
                session_id=request.session_id,
                demasked_response=original_text
            )

        raise HTTPException(
            status_code=400,
            detail="Invalid flow: provide user_input OR (llm_response + session_id)"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM flow failed: {str(e)}")


@app.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    store: Optional[NATSSessionStore] = Depends(get_store),
):
    """
    Clear session data.

    Should be called after LLM workflow is complete to free memory.
    When using NATS, sessions expire automatically based on TTL.
    """
    deleted = False

    # Delete from NATS if available
    if store:
        deleted = await store.delete_session(session_id)

    # Also clear from in-memory storage
    filter_instance.clear_session(session_id)

    return {"status": "cleared", "session_id": session_id, "nats_deleted": deleted}


@app.get("/health")
async def health_check(store: Optional[NATSSessionStore] = Depends(get_store)):
    """Health check endpoint including NATS connectivity."""
    health = {
        "status": "healthy",
        "gliner_enabled": filter_instance.use_gliner,
        "active_sessions": len(filter_instance.sessions),
        "nats_enabled": app.state.use_nats,
    }

    if store:
        try:
            await store._kv.status()
            health["nats_status"] = "connected"
        except Exception as e:
            health["nats_status"] = f"error: {e}"

    return health


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=1001)

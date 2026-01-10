"""
FastAPI endpoint for privacy filter with reversible masking
"""

from typing import Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from privacy_filter import PrivacyFilter

app = FastAPI(
    title="Privacy Filter API",
    description="Mask and de-mask sensitive data using GLiNER + Presidio",
    version="1.0.0"
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


# API Endpoints

@app.post("/mask", response_model=MaskResponse)
async def mask_text(request: MaskRequest):
    """
    Mask sensitive data in text

    Returns masked text and session ID for de-masking
    """
    try:
        result = filter_instance.mask(request.text, request.entities_to_mask)
        return MaskResponse(
            masked_text=result.masked_text,
            session_id=result.session_id,
            entities_found=len(result.entities_found),
            token_map=result.token_map
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Masking failed: {str(e)}")


@app.post("/demask", response_model=DemaskResponse)
async def demask_text(request: DemaskRequest):
    """
    Restore original text using session ID

    De-masks tokens using stored token map from masking operation
    """
    try:
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


@app.post("/llm-flow", response_model=LLMFlowResponse)
async def llm_flow(request: LLMFlowRequest):
    """
    Complete LLM workflow with privacy protection

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
            return LLMFlowResponse(
                masked_input=mask_result.masked_text,
                session_id=mask_result.session_id,
                demasked_response=None
            )

        # Step 2: De-mask LLM response (if session_id provided)
        if request.llm_response:
            demask_result = filter_instance.demask(
                request.llm_response,
                session_id=request.session_id
            )
            return LLMFlowResponse(
                masked_input="",  # Already processed
                session_id=request.session_id,
                demasked_response=demask_result.original_text
            )

        raise HTTPException(
            status_code=400,
            detail="Invalid flow: provide user_input OR (llm_response + session_id)"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM flow failed: {str(e)}")


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """
    Clear session data

    Should be called after LLM workflow is complete to free memory
    """
    filter_instance.clear_session(session_id)
    return {"status": "cleared", "session_id": session_id}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "gliner_enabled": filter_instance.use_gliner,
        "active_sessions": len(filter_instance.sessions)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

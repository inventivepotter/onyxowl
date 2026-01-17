"""
Simple Privacy Filter with GLiNER + Presidio
Hash map-based reversible masking/de-masking
"""

from typing import Dict, List, Tuple, Optional
import hashlib
import uuid
from dataclasses import dataclass, field
from enum import Enum

# Dependencies - install with: pip install presidio-analyzer presidio-anonymizer gliner
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from gliner import GLiNER


class EntityType(str, Enum):
    """Entity types for detection"""
    # Personal Info
    PERSON = "PERSON"
    EMAIL = "EMAIL_ADDRESS"
    PHONE = "PHONE_NUMBER"
    SSN = "US_SSN"

    # Financial
    CREDIT_CARD = "CREDIT_CARD"
    BITCOIN = "BITCOIN_ADDRESS"
    ETHEREUM = "ETHEREUM_ADDRESS"
    IBAN = "IBAN_CODE"

    # Secrets
    AWS_KEY = "AWS_ACCESS_KEY_ID"
    API_KEY = "API_KEY"
    PASSWORD = "PASSWORD"
    JWT = "JWT_TOKEN"

    # Location
    ADDRESS = "LOCATION"
    IP_ADDRESS = "IP_ADDRESS"

    # Health
    MEDICAL_LICENSE = "MEDICAL_LICENSE"


@dataclass
class MaskingResult:
    """Result of masking operation"""
    masked_text: str
    token_map: Dict[str, str]  # masked_token -> original_value
    entities_found: List[Dict]
    session_id: str


@dataclass
class DemaskingResult:
    """Result of de-masking operation"""
    original_text: str
    entities_restored: int


class GLiNERPresidioEngine:
    """Custom Presidio NLP engine using GLiNER"""

    def __init__(self, model_name: str = "urchade/gliner_medium-v2.1"):
        """
        Initialize GLiNER model

        Args:
            model_name: HuggingFace model name for GLiNER
        """
        print(f"Loading GLiNER model: {model_name}")
        self.gliner_model = GLiNER.from_pretrained(model_name)

        # Entity labels for GLiNER to detect
        self.entity_labels = [
            "person", "email", "phone number", "social security number",
            "credit card", "bitcoin address", "ethereum address", "IBAN",
            "AWS key", "API key", "password", "JWT token",
            "address", "IP address", "medical license"
        ]

    def analyze(self, text: str, language: str = "en") -> List[Dict]:
        """
        Analyze text using GLiNER + regex fallback

        Args:
            text: Input text to analyze
            language: Language code (default: en)

        Returns:
            List of detected entities
        """
        # Handle empty text
        if not text or not text.strip():
            return []

        presidio_entities = []

        # Use GLiNER for entity detection
        try:
            entities = self.gliner_model.predict_entities(
                text,
                self.entity_labels,
                threshold=0.5  # Confidence threshold
            )

            # Convert GLiNER output to Presidio format
            for entity in entities:
                presidio_entities.append({
                    "entity_type": self._map_gliner_to_presidio(entity["label"]),
                    "start": entity["start"],
                    "end": entity["end"],
                    "score": entity["score"],
                    "text": text[entity["start"]:entity["end"]]
                })
        except Exception as e:
            print(f"GLiNER detection failed: {e}, using regex fallback")

        # Add regex-based detection for common patterns (fallback)
        regex_entities = self._regex_detect(text)
        presidio_entities.extend(regex_entities)

        # Remove duplicates (prefer higher confidence)
        presidio_entities = self._deduplicate_entities(presidio_entities)

        return presidio_entities

    def _map_gliner_to_presidio(self, gliner_label: str) -> str:
        """Map GLiNER labels to Presidio entity types"""
        mapping = {
            "person": "PERSON",
            "email": "EMAIL_ADDRESS",
            "phone number": "PHONE_NUMBER",
            "social security number": "US_SSN",
            "credit card": "CREDIT_CARD",
            "bitcoin address": "BITCOIN_ADDRESS",
            "ethereum address": "ETHEREUM_ADDRESS",
            "IBAN": "IBAN_CODE",
            "AWS key": "AWS_ACCESS_KEY_ID",
            "API key": "API_KEY",
            "password": "PASSWORD",
            "JWT token": "JWT_TOKEN",
            "address": "LOCATION",
            "IP address": "IP_ADDRESS",
            "medical license": "MEDICAL_LICENSE"
        }
        return mapping.get(gliner_label, gliner_label.upper().replace(" ", "_"))

    def _regex_detect(self, text: str) -> List[Dict]:
        """
        Regex-based entity detection as fallback

        Args:
            text: Input text

        Returns:
            List of detected entities
        """
        import re

        entities = []

        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            entities.append({
                "entity_type": "EMAIL_ADDRESS",
                "start": match.start(),
                "end": match.end(),
                "score": 0.95,  # High confidence for regex
                "text": match.group()
            })

        # Phone pattern (simple)
        phone_pattern = r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        for match in re.finditer(phone_pattern, text):
            entities.append({
                "entity_type": "PHONE_NUMBER",
                "start": match.start(),
                "end": match.end(),
                "score": 0.9,
                "text": match.group()
            })

        # SSN pattern
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        for match in re.finditer(ssn_pattern, text):
            entities.append({
                "entity_type": "US_SSN",
                "start": match.start(),
                "end": match.end(),
                "score": 0.95,
                "text": match.group()
            })

        # Credit card pattern (simple)
        cc_pattern = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        for match in re.finditer(cc_pattern, text):
            entities.append({
                "entity_type": "CREDIT_CARD",
                "start": match.start(),
                "end": match.end(),
                "score": 0.9,
                "text": match.group()
            })

        return entities

    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """
        Remove duplicate entities, keeping highest confidence

        Args:
            entities: List of entities

        Returns:
            Deduplicated list
        """
        if not entities:
            return []

        # Sort by position
        entities = sorted(entities, key=lambda x: (x["start"], x["end"]))

        deduplicated = []
        skip_until = -1

        for entity in entities:
            # Skip if this entity overlaps with a previous one we're keeping
            if entity["start"] < skip_until:
                continue

            # Check for overlapping entities
            overlapping = [
                e for e in entities
                if (e["start"] <= entity["start"] < e["end"] or
                    entity["start"] <= e["start"] < entity["end"])
            ]

            if overlapping:
                # Keep the one with highest confidence
                best = max(overlapping, key=lambda x: x["score"])
                if best not in deduplicated:
                    deduplicated.append(best)
                    skip_until = best["end"]
            else:
                deduplicated.append(entity)
                skip_until = entity["end"]

        return deduplicated


class PrivacyFilter:
    """
    Privacy filter with reversible masking using hash maps
    """

    def __init__(self, use_gliner: bool = True):
        """
        Initialize privacy filter

        Args:
            use_gliner: Use GLiNER for entity detection (recommended)
        """
        self.use_gliner = use_gliner

        if use_gliner:
            # Initialize GLiNER engine
            self.gliner_engine = GLiNERPresidioEngine()

        # Initialize Presidio analyzer (we'll use custom GLiNER results)
        self.analyzer = AnalyzerEngine()

        # Initialize Presidio anonymizer
        self.anonymizer = AnonymizerEngine()

        # Session storage: session_id -> token_map
        self.sessions: Dict[str, Dict[str, str]] = {}

    def _generate_token(self, entity_type: str, index: int) -> str:
        """
        Generate a unique masked token

        Args:
            entity_type: Type of entity
            index: Index of this entity in the text

        Returns:
            Masked token like <EMAIL_ADDRESS_1>
        """
        return f"<{entity_type}_{index}>"

    def mask(self, text: str, entities_to_mask: Optional[List[str]] = None) -> MaskingResult:
        """
        Mask sensitive entities in text and create reversible token map

        Args:
            text: Input text to mask
            entities_to_mask: List of entity types to mask (None = all)

        Returns:
            MaskingResult with masked text and token map
        """
        session_id = str(uuid.uuid4())

        # Detect entities using GLiNER
        if self.use_gliner:
            detected_entities = self.gliner_engine.analyze(text)
        else:
            # Fallback to Presidio's default
            results = self.analyzer.analyze(text, language="en")
            detected_entities = [
                {
                    "entity_type": r.entity_type,
                    "start": r.start,
                    "end": r.end,
                    "score": r.score,
                    "text": text[r.start:r.end]
                }
                for r in results
            ]

        # Filter entities if specified
        if entities_to_mask:
            detected_entities = [
                e for e in detected_entities
                if e["entity_type"] in entities_to_mask
            ]

        # Sort entities by start position (reverse to replace from end to start)
        detected_entities.sort(key=lambda x: x["start"], reverse=True)

        # Create token map and masked text
        token_map = {}  # masked_token -> original_value
        masked_text = text
        entity_counts: Dict[str, int] = {}

        for entity in detected_entities:
            entity_type = entity["entity_type"]
            original_value = entity["text"]

            # Count entity type for unique token generation
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1

            # Generate unique token
            masked_token = self._generate_token(entity_type, entity_counts[entity_type])

            # Store in token map
            token_map[masked_token] = original_value

            # Replace in text
            start, end = entity["start"], entity["end"]
            masked_text = masked_text[:start] + masked_token + masked_text[end:]

        # Store session
        self.sessions[session_id] = token_map

        return MaskingResult(
            masked_text=masked_text,
            token_map=token_map,
            entities_found=detected_entities,
            session_id=session_id
        )

    def demask(self, masked_text: str, session_id: Optional[str] = None,
               token_map: Optional[Dict[str, str]] = None) -> DemaskingResult:
        """
        Restore original text using token map

        Args:
            masked_text: Text with masked tokens
            session_id: Session ID to retrieve token map
            token_map: Direct token map (alternative to session_id)

        Returns:
            DemaskingResult with restored text
        """
        # Get token map
        if token_map is None:
            if session_id is None:
                raise ValueError("Must provide either session_id or token_map")
            token_map = self.sessions.get(session_id, {})

        # Restore text
        original_text = masked_text
        entities_restored = 0

        for masked_token, original_value in token_map.items():
            if masked_token in original_text:
                original_text = original_text.replace(masked_token, original_value)
                entities_restored += 1

        return DemaskingResult(
            original_text=original_text,
            entities_restored=entities_restored
        )

    def clear_session(self, session_id: str):
        """Clear session data"""
        if session_id in self.sessions:
            del self.sessions[session_id]


# Simple API Endpoint Example (FastAPI)
# Uncomment to use:
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
filter_instance = PrivacyFilter(use_gliner=True)


class MaskRequest(BaseModel):
    text: str
    entities_to_mask: Optional[List[str]] = None


class MaskResponse(BaseModel):
    masked_text: str
    session_id: str
    entities_found: int


class DemaskRequest(BaseModel):
    masked_text: str
    session_id: str


class DemaskResponse(BaseModel):
    original_text: str
    entities_restored: int


@app.post("/mask", response_model=MaskResponse)
async def mask_text(request: MaskRequest):
    '''Mask sensitive data in text'''
    try:
        result = filter_instance.mask(request.text, request.entities_to_mask)
        return MaskResponse(
            masked_text=result.masked_text,
            session_id=result.session_id,
            entities_found=len(result.entities_found)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/demask", response_model=DemaskResponse)
async def demask_text(request: DemaskRequest):
    '''Restore original text using session ID'''
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
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    '''Clear session data'''
    filter_instance.clear_session(session_id)
    return {"status": "cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=1001)
"""

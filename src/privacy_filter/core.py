"""
Core Privacy Filter implementation
Hash map-based reversible masking/de-masking
"""

import uuid
from typing import Dict, List, Optional

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

from .gliner_engine import GLiNERPresidioEngine
from .models import MaskingResult, DemaskingResult


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

        # Initialize Presidio analyzer (fallback)
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

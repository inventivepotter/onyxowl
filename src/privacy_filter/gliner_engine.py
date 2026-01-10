"""
GLiNER-based entity recognition engine
Hybrid approach: GLiNER (ML) + Regex (patterns)
"""

import re
from typing import Dict, List

from gliner import GLiNER

from .patterns import compile_all_patterns


class GLiNERPresidioEngine:
    """Custom Presidio NLP engine using GLiNER + Regex"""

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

        # Compile regex patterns
        self.compiled_patterns = compile_all_patterns()

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
        Regex-based entity detection using comprehensive patterns

        Args:
            text: Input text

        Returns:
            List of detected entities
        """
        entities = []

        # Apply all compiled patterns
        for entity_type, patterns in self.compiled_patterns.items():
            for pattern, pattern_name in patterns:
                for match in pattern.finditer(text):
                    entities.append({
                        "entity_type": entity_type,
                        "start": match.start(),
                        "end": match.end(),
                        "score": 0.95,  # High confidence for regex
                        "text": match.group(),
                        "pattern": pattern_name
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

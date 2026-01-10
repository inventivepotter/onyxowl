"""
Pre-download GLiNER model for Docker image caching
This ensures the model is included in the Docker image
"""

import os
from gliner import GLiNER

def download_gliner_model():
    """Download GLiNER model to cache"""
    print("Downloading GLiNER model...")
    print("Model: urchade/gliner_medium-v2.1 (~400MB)")

    try:
        # This will download and cache the model
        model = GLiNER.from_pretrained("urchade/gliner_medium-v2.1")
        print("✓ GLiNER model downloaded successfully")

        # Test prediction to ensure it works
        test_text = "Email me at test@example.com"
        entities = model.predict_entities(test_text, ["email"], threshold=0.5)
        print(f"✓ Model test successful - detected {len(entities)} entities")

        return True
    except Exception as e:
        print(f"⚠ Warning: Failed to download GLiNER model: {e}")
        print("Model will be downloaded on first API request")
        return False

if __name__ == "__main__":
    download_gliner_model()

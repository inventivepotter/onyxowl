"""
Pre-download GLiNER model for Docker image caching
This ensures the model is included in the Docker image
"""

import os

# Set timeout for Hugging Face downloads (in seconds)
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "300")
os.environ.setdefault("REQUESTS_TIMEOUT", "300")

from huggingface_hub import snapshot_download
from gliner import GLiNER

def download_gliner_model():
    """Download GLiNER model to cache"""
    print("Downloading GLiNER model...")
    print("Model: urchade/gliner_medium-v2.1 (~400MB)")

    try:
        # Pre-download model files with explicit timeout and resume support
        model_id = "urchade/gliner_medium-v2.1"
        print("Fetching model files from Hugging Face...")
        snapshot_download(
            repo_id=model_id,
            resume_download=True,
            max_workers=1,  # Single thread to avoid connection issues
        )
        print("✓ Model files downloaded")

        # Load the model to verify it works
        model = GLiNER.from_pretrained(model_id)
        print("✓ GLiNER model loaded successfully")

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

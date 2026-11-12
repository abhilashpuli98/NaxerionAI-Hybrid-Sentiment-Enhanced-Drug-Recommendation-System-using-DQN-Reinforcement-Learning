#!/usr/bin/env python3
"""
SEDRS — Model Weight Verification Script
=========================================
IEEE Methodology: This script verifies that all required pre-trained model
weights are accessible before the system starts. It downloads them from
HuggingFace Hub / PyTorch Hub if not already cached.

Models Verified
---------------
1. Text:  cardiffnlp/twitter-roberta-base-sentiment  (HuggingFace)
2. Audio: ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition  (HuggingFace)
3. Image: openai/clip-vit-base-patch32  (HuggingFace)
4. Image Fallback: torchvision ResNet50 (DEFAULT weights)
5. DQN:  local checkpoint (models/dqn_agent.pth) — created at first training

Running
-------
    python verify_weights.py
"""

import os
import sys
import ssl
import time

# ─── SSL Fix (Windows) ──────────────────────────────────────────────────────
try:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    os.environ['CURL_CA_BUNDLE'] = certifi.where()
except ImportError:
    pass

# ─── Configuration ──────────────────────────────────────────────────────────
MODELS = {
    'Text Sentiment (RoBERTa)': {
        'type': 'huggingface',
        'model_id': 'cardiffnlp/twitter-roberta-base-sentiment',
        'task': 'sentiment-analysis',
    },
    'Audio Emotion (Wav2Vec2)': {
        'type': 'huggingface',
        'model_id': 'ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition',
        'task': 'audio-classification',
    },
    'Image Drug Validation (CLIP)': {
        'type': 'huggingface',
        'model_id': 'openai/clip-vit-base-patch32',
        'task': 'zero-shot-image-classification',
    },
    'Image Fallback (ResNet50)': {
        'type': 'torchvision',
        'model': 'resnet50',
    },
}

PASS = '\033[92m✓\033[0m'
FAIL = '\033[91m✗\033[0m'
WARN = '\033[93m⚠\033[0m'


def verify_huggingface(name: str, cfg: dict) -> bool:
    """Download / verify a HuggingFace pipeline model."""
    try:
        from transformers import pipeline as hf_pipeline
        print(f"  Downloading {cfg['model_id']} …", end=' ', flush=True)
        t0 = time.time()
        hf_pipeline(cfg['task'], model=cfg['model_id'], device=-1)
        dt = time.time() - t0
        print(f"OK ({dt:.1f}s)")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False


def verify_torchvision(name: str, cfg: dict) -> bool:
    """Download / verify a TorchVision model."""
    try:
        import torch
        from torchvision.models import resnet50, ResNet50_Weights
        print(f"  Downloading ResNet50 (ImageNet) …", end=' ', flush=True)
        t0 = time.time()
        weights = ResNet50_Weights.DEFAULT
        model = resnet50(weights=weights)
        model.eval()
        _ = weights.transforms()
        dt = time.time() - t0
        print(f"OK ({dt:.1f}s)")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False


def verify_local_checkpoint(path: str) -> bool:
    """Check if a local .pth checkpoint exists."""
    if os.path.exists(path):
        size_kb = os.path.getsize(path) / 1024
        print(f"  Found {path} ({size_kb:.0f} KB)")
        return True
    else:
        print(f"  {WARN} Not found: {path} (will be created on first training)")
        return True  # Not a failure — it's optional


def main():
    print("=" * 70)
    print("SEDRS — Model Weight Verification")
    print("=" * 70)

    results = {}

    for name, cfg in MODELS.items():
        print(f"\n[{name}]")
        if cfg['type'] == 'huggingface':
            results[name] = verify_huggingface(name, cfg)
        elif cfg['type'] == 'torchvision':
            results[name] = verify_torchvision(name, cfg)

    # Check local DQN checkpoint
    print(f"\n[DQN Agent Checkpoint]")
    dqn_ok = verify_local_checkpoint('models/dqn_agent.pth')
    results['DQN Agent'] = dqn_ok

    # Check models directory
    os.makedirs('models', exist_ok=True)

    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    all_ok = True
    for name, ok in results.items():
        status = PASS if ok else FAIL
        print(f"  {status}  {name}")
        if not ok:
            all_ok = False

    if all_ok:
        print(f"\n{PASS} All models verified and ready.")
        return 0
    else:
        print(f"\n{FAIL} Some models failed verification. Check errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

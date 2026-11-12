"""
Image Drug Validation Module — Production-Ready
================================================
Primary  : OpenAI CLIP zero-shot classification via HuggingFace pipeline.
           Model: openai/clip-vit-base-patch32
           Task : Determine whether the uploaded image is "a drug/medicine/pill"
                  or an unrelated object.

Fallback : ResNet50 (ImageNet weights) + keyword matching on predicted categories.

IEEE Reference:
  Model  : openai/clip-vit-base-patch32
  Source : https://huggingface.co/openai/clip-vit-base-patch32
  Paper  : Radford et al., "Learning Transferable Visual Models From Natural
           Language Supervision," ICML 2021.
  Labels : 3-class — "valid medication" / "expired or damaged medication" /
                       "unrelated object, not a drug"

Model Loading: Singleton pattern — downloaded ONCE at first call.
"""

import os
import logging
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ─────────────────────────────────────────────────────────────────────────────
# CLIP candidate labels  →  map to our 3-class output
# ─────────────────────────────────────────────────────────────────────────────
_CLIP_LABELS = [
    "a valid pharmaceutical drug, pill, or medicine",        # → class 2  (Valid)
    "an expired, damaged, or counterfeit medication",        # → class 1  (Uncertain/Expired)
    "an unrelated object, not a drug or medication",         # → class 0  (Invalid)
]
_LABEL_TO_CLASS = {0: 2, 1: 1, 2: 0}   # CLIP rank → our class int

VALIDITY_CLASSES = {0: "Invalid", 1: "Uncertain / Expired", 2: "Valid"}

# ─────────────────────────────────────────────────────────────────────────────
# Singleton: load CLIP pipeline once
# ─────────────────────────────────────────────────────────────────────────────
_clip_pipeline = None
_clip_loaded   = False


def _get_clip_pipeline():
    """Return the HuggingFace zero-shot-image-classification pipeline (singleton)."""
    global _clip_pipeline, _clip_loaded

    if _clip_loaded:
        return _clip_pipeline

    _clip_loaded = True
    try:
        from transformers import pipeline as hf_pipeline

        logger.info("Loading CLIP zero-shot image classification model …")
        _clip_pipeline = hf_pipeline(
            "zero-shot-image-classification",
            model="openai/clip-vit-base-patch32",
            device=-1,       # CPU; use 0 for GPU
        )
        logger.info("CLIP model loaded successfully ✓")
    except Exception as e:
        logger.error(f"CLIP model load failed: {e}. Will use ResNet50 fallback.")
        _clip_pipeline = None

    return _clip_pipeline


# ─────────────────────────────────────────────────────────────────────────────
# ResNet50 fallback (ImageNet keyword matching)
# ─────────────────────────────────────────────────────────────────────────────
_resnet_model      = None
_resnet_transforms = None
_resnet_categories = None
_resnet_loaded     = False

_VALID_KEYWORDS = [
    "bottle", "pill", "syringe", "capsule", "tablet", "drug", "medicine",
    "vial", "bandage", "stethoscope", "cup", "container", "packet", "lab",
    "monitor", "dropper", "lotion", "inhaler", "test tube", "beaker",
]


def _get_resnet():
    """Lazy-load ResNet50 with ImageNet weights (singleton)."""
    global _resnet_model, _resnet_transforms, _resnet_categories, _resnet_loaded

    if _resnet_loaded:
        return _resnet_model, _resnet_transforms, _resnet_categories

    _resnet_loaded = True
    try:
        import torch
        from torchvision.models import resnet50, ResNet50_Weights

        logger.info("Loading ResNet50 (ImageNet) fallback …")
        weights           = ResNet50_Weights.DEFAULT
        model             = resnet50(weights=weights)
        model.eval()
        _resnet_model      = model
        _resnet_transforms = weights.transforms()
        _resnet_categories = weights.meta["categories"]
        logger.info("ResNet50 fallback loaded ✓")
    except Exception as e:
        logger.error(f"ResNet50 fallback load failed: {e}")
        _resnet_model, _resnet_transforms, _resnet_categories = None, None, None

    return _resnet_model, _resnet_transforms, _resnet_categories


# ─────────────────────────────────────────────────────────────────────────────
# Public Analyser Class
# ─────────────────────────────────────────────────────────────────────────────
class ImageDrugAnalyzer:
    """
    Drug image validation using CLIP zero-shot classification.

    Output classes
    --------------
    0 = Invalid  (not a medication)
    1 = Uncertain / Expired
    2 = Valid    (confirmed medication)

    Usage
    -----
    >>> analyzer = ImageDrugAnalyzer()
    >>> preds, confs = analyzer.predict("drug_image.jpg")
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton — one instance per process."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, num_classes: int = 3, device: str = "cpu"):
        if self._initialized:
            return
        self._initialized = True
        self.device       = device
        self.num_classes  = num_classes

        # Pre-warm CLIP pipeline
        _get_clip_pipeline()
        # Pre-warm ResNet50 fallback
        _get_resnet()

    # ── CLIP-based prediction ─────────────────────────────────────────────
    def _predict_clip(self, image_path: str):
        """Run CLIP zero-shot classification on one image."""
        pipe = _get_clip_pipeline()
        if pipe is None:
            return None, 0.0
        try:
            img     = Image.open(image_path).convert("RGB")
            results = pipe(img, candidate_labels=_CLIP_LABELS)
            # results: [{'label': '...', 'score': 0.9}, ...]
            # sorted by descending score
            top         = results[0]
            top_rank    = _CLIP_LABELS.index(top["label"])
            pred_class  = _LABEL_TO_CLASS[top_rank]
            confidence  = float(top["score"])
            logger.debug(f"CLIP result: {top['label']!r} → class {pred_class} ({confidence:.3f})")
            return pred_class, confidence
        except Exception as e:
            logger.error(f"CLIP inference error: {e}")
            return None, 0.0

    # ── ResNet50 fallback prediction ──────────────────────────────────────
    def _predict_resnet(self, image_path: str):
        """Keyword-match ResNet50 ImageNet predictions for drug-validity scoring."""
        import torch
        model, tfm, cats = _get_resnet()
        if model is None:
            return 1, 0.0   # Uncertain fallback

        try:
            img    = Image.open(image_path).convert("RGB")
            batch  = tfm(img).unsqueeze(0)
            with torch.no_grad():
                logits = model(batch).squeeze(0)
                probs  = logits.softmax(0)
            top5_prob, top5_idx = torch.topk(probs, 5)

            is_valid   = False
            max_prob   = 0.0
            for i in range(5):
                cat_name = cats[top5_idx[i].item()].lower()
                prob     = top5_prob[i].item()
                if any(kw in cat_name for kw in _VALID_KEYWORDS):
                    is_valid = True
                    max_prob = max(max_prob, prob)

            if is_valid:
                pred = 2 if max_prob > 0.10 else 1
                conf = max_prob
            else:
                # Penalise clearly unrelated categories
                top_cat  = cats[top5_idx[0].item()].lower()
                unrelated = ["dog", "cat", "car", "truck", "bird", "fish",
                             "person", "face", "food", "flower"]
                pred = 0 if any(u in top_cat for u in unrelated) else 1
                conf = float(top5_prob[0].item())
            return pred, conf

        except Exception as e:
            logger.error(f"ResNet50 inference error: {e}")
            return 1, 0.0

    # ── Public API ────────────────────────────────────────────────────────
    def predict(self, image_paths):
        """
        Predict drug validity for one or more image files.

        Parameters
        ----------
        image_paths : str | list[str]

        Returns
        -------
        predictions : np.ndarray  int  {0, 1, 2}
        confidences : np.ndarray  float [0, 1]
        """
        if isinstance(image_paths, str):
            image_paths = [image_paths]

        predictions, confidences = [], []

        for path in image_paths:
            if not os.path.exists(path):
                logger.warning(f"Image file not found: {path}. Returning Uncertain.")
                predictions.append(1)
                confidences.append(0.0)
                continue

            # Try CLIP first
            pred, conf = self._predict_clip(path)
            if pred is None:
                # Fallback to ResNet50
                pred, conf = self._predict_resnet(path)
                logger.debug(f"Using ResNet50 fallback for {path}")

            predictions.append(pred)
            confidences.append(conf)

        return np.array(predictions, dtype=int), np.array(confidences, dtype=float)

    def predict_label(self, image_path: str) -> dict:
        """
        Convenience method.

        Returns
        -------
        {"label": "Valid", "confidence": 0.91, "pred_idx": 2}
        """
        preds, confs = self.predict(image_path)
        idx  = int(preds[0])
        conf = float(confs[0])
        return {
            "label":      VALIDITY_CLASSES.get(idx, "Uncertain"),
            "confidence": conf,
            "pred_idx":   idx,
        }

    # ── Legacy stubs (keep API-compatible with older callers) ─────────────
    def load_model(self, path):
        """No-op: weights managed by HuggingFace hub cache."""
        pass

    def save_model(self, path):
        """No-op: CLIP weights are read-only pre-trained."""
        pass

    def train(self, *args, **kwargs):
        """
        CLIP zero-shot requires no training.
        To fine-tune ResNet50 on a custom drug dataset, use train_image_model.py.
        """
        logger.info("CLIP zero-shot needs no training. "
                    "Use train_image_model.py for ResNet50 fine-tuning.")

    def evaluate(self, image_paths: list, labels: list) -> float:
        """Compute classification accuracy on a labelled set."""
        preds, _ = self.predict(image_paths)
        return float(np.mean(preds == np.array(labels)))

"""HuggingFace Transformer-based Text Sentiment Analysis Module"""

import torch
import numpy as np
from transformers import pipeline
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextSentimentAnalyzer:
    """
    Text sentiment analysis using HuggingFace Transformers.
    Uses 'cardiffnlp/twitter-roberta-base-sentiment' which outputs:
    Label 0 -> Negative
    Label 1 -> Neutral
    Label 2 -> Positive
    """
    def __init__(self, device='cpu'):
        self.device = 0 if torch.cuda.is_available() and device != 'cpu' else -1
        logger.info(f"Loading Text Sentiment Model (cardiffnlp/twitter-roberta-base-sentiment) on device {self.device}...")
        try:
            self.pipeline = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment",
                device=self.device
            )
            logger.info("Text Sentiment Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load text sentiment model: {e}")
            self.pipeline = None

    def predict(self, texts):
        """
        Predict sentiment for given texts.
        Returns: (predictions, confidences) as numpy arrays.
        Predictions: 0=Negative, 1=Neutral, 2=Positive
        """
        if not self.pipeline:
            logger.warning("Model not loaded, returning defaults.")
            return np.array([1]*len(texts)), np.array([0.0]*len(texts))

        if isinstance(texts, str):
            texts = [texts]
            
        predictions = []
        confidences = []
        
        try:
            # Pipeline returns list of dicts: [{'label': 'LABEL_0', 'score': 0.9}, ...]
            # or [{'label': 'Negative', 'score': ...}] depending on model config
            # cardiffnlp model config maps: LABEL_0->Negative, LABEL_1->Neutral, LABEL_2->Positive
            results = self.pipeline(texts, truncation=True, max_length=512)
            
            for res in results:
                label_str = res['label']
                score = res['score']
                
                # Map label to 0, 1, 2
                # The model typically returns LABEL_0, LABEL_1, LABEL_2
                # But newer transformers instructions might map them.
                # We handle both just in case.
                if 'LABEL_0' in label_str or 'NEGATIVE' in label_str.upper():
                    pred = 0
                elif 'LABEL_1' in label_str or 'NEUTRAL' in label_str.upper():
                    pred = 1
                elif 'LABEL_2' in label_str or 'POSITIVE' in label_str.upper():
                    pred = 2
                else:
                    pred = 1 # Default neutral
                
                predictions.append(pred)
                confidences.append(score)
                
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            for _ in texts:
                predictions.append(1)
                confidences.append(0.0)
                
        return np.array(predictions), np.array(confidences)

    # Legacy methods to prevent crashes validation
    def load_model(self, path):
        pass
        
    def save_model(self, path):
        pass


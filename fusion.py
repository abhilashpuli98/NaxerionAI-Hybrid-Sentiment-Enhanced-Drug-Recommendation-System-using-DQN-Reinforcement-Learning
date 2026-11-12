"""Multi-Modal Fusion Mechanism"""

import numpy as np
import torch
from config import WEIGHT_TEXT, WEIGHT_AUDIO, WEIGHT_IMAGE, SENTIMENT_CLASSES, EMOTION_CLASSES, DRUG_VALIDITY_CLASSES

class MultiModalFusion:
    """Fusion layer for combining multi-modal sentiment outputs"""
    
    def __init__(self, weight_text=WEIGHT_TEXT, weight_audio=WEIGHT_AUDIO, weight_image=WEIGHT_IMAGE):
        self.weight_text = weight_text
        self.weight_audio = weight_audio
        self.weight_image = weight_image
        self.normalize_weights()
        
    def normalize_weights(self):
        """Normalize weights to sum to 1"""
        total_weight = self.weight_text + self.weight_audio + self.weight_image
        self.weight_text /= total_weight
        self.weight_audio /= total_weight
        self.weight_image /= total_weight
    
    def dynamic_weight_adjustment(self, text_confidence, audio_confidence, image_confidence):
        """Dynamically adjust weights based on confidence scores"""
        total_confidence = text_confidence + audio_confidence + image_confidence
        
        if total_confidence > 0:
            self.weight_text = (WEIGHT_TEXT * text_confidence) / total_confidence
            self.weight_audio = (WEIGHT_AUDIO * audio_confidence) / total_confidence
            self.weight_image = (WEIGHT_IMAGE * image_confidence) / total_confidence
        else:
            self.normalize_weights()
    
    def fuse_sentiments(self, text_pred, text_conf, audio_pred, audio_conf, image_pred, image_conf):
        """
        Fuse multi-modal sentiment predictions
        
        Args:
            text_pred: text sentiment prediction (0-2)
            text_conf: text confidence score
            audio_pred: audio emotion prediction (0-6)
            audio_conf: audio confidence score
            image_pred: image validity prediction (0-2)
            image_conf: image confidence score
        
        Returns:
            fused_score: overall sentiment score
            confidence: overall confidence
        """
        # Adjust weights based on confidence
        self.dynamic_weight_adjustment(text_conf, audio_conf, image_conf)
        
        # Normalize predictions to sentiment scale (0-2)
        text_score = text_pred
        audio_score = self._map_emotion_to_sentiment(audio_pred)
        image_score = image_pred
        
        # Weighted fusion
        fused_score = (self.weight_text * text_score + 
                      self.weight_audio * audio_score + 
                      self.weight_image * image_score)
        
        # Confidence fusion (arithmetic mean with weight adjustment)
        confidence = (self.weight_text * text_conf + 
                     self.weight_audio * audio_conf + 
                     self.weight_image * image_conf)
        
        return fused_score, confidence
    
    def _map_emotion_to_sentiment(self, emotion_pred):
        """
        Map emotion prediction to sentiment scale
        Emotions: 0=angry, 1=disgust, 2=fear, 3=happy, 4=neutral, 5=sad, 6=surprise
        Sentiment: 0=negative, 1=neutral, 2=positive
        """
        emotion_to_sentiment = {
            0: 0,  # angry -> negative
            1: 0,  # disgust -> negative
            2: 0,  # fear -> negative
            3: 2,  # happy -> positive
            4: 1,  # neutral -> neutral
            5: 0,  # sad -> negative
            6: 2   # surprise -> positive
        }
        return emotion_to_sentiment.get(emotion_pred, 1)
    
    def create_fusion_report(self, text_pred, text_conf, audio_pred, audio_conf, 
                            image_pred, image_conf, drug_name):
        """Create a detailed fusion report"""
        fused_score, confidence = self.fuse_sentiments(
            text_pred, text_conf, audio_pred, audio_conf, image_pred, image_conf
        )
        
        report = {
            'drug_name': drug_name,
            'text_sentiment': SENTIMENT_CLASSES.get(text_pred, 'Unknown'),
            'text_confidence': round(float(text_conf), 4),
            'audio_emotion': EMOTION_CLASSES.get(audio_pred, 'Unknown'),
            'audio_confidence': round(float(audio_conf), 4),
            'image_validity': DRUG_VALIDITY_CLASSES.get(image_pred, 'Unknown'),
            'image_confidence': round(float(image_conf), 4),
            'fused_sentiment_score': round(float(fused_score), 4),
            'overall_confidence': round(float(confidence), 4),
            'weight_text': round(self.weight_text, 4),
            'weight_audio': round(self.weight_audio, 4),
            'weight_image': round(self.weight_image, 4)
        }
        
        return report

class AdvancedFusion:
    """Advanced fusion with attention mechanism"""
    
    def __init__(self, fusion_dim=256):
        self.fusion_dim = fusion_dim
        self.fusion_weights = None
        self.attention_scores = None
        
    def attention_fusion(self, text_features, audio_features, image_features):
        """
        Fusion with attention mechanism
        Computes attention weights for each modality
        """
        # Stack features
        features = np.stack([text_features, audio_features, image_features])
        
        # Compute attention weights using softmax
        attention_scores = np.exp(features) / np.sum(np.exp(features))
        self.attention_scores = attention_scores
        
        # Weighted sum
        fused_features = np.sum(features * attention_scores, axis=0)
        
        return fused_features, attention_scores
    
    def early_fusion(self, text_features, audio_features, image_features):
        """Early fusion: concatenate features"""
        fused = np.concatenate([text_features, audio_features, image_features])
        return fused
    
    def late_fusion(self, text_output, audio_output, image_output, weights=None):
        """Late fusion: combine decision scores"""
        if weights is None:
            weights = np.array([WEIGHT_TEXT, WEIGHT_AUDIO, WEIGHT_IMAGE])
        
        weights = weights / np.sum(weights)
        fused_output = (weights[0] * text_output + 
                       weights[1] * audio_output + 
                       weights[2] * image_output)
        
        return fused_output

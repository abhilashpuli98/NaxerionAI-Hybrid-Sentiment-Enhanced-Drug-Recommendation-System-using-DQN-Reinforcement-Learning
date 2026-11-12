"""Configuration file for the drug recommendation system"""

# Model paths
BERT_MODEL = "distilbert-base-uncased"
RESNET50_WEIGHTS = "DEFAULT"

# Training parameters
BATCH_SIZE = 16
BATCH_SIZE_BERT = 16
LEARNING_RATE_BERT = 2e-5
LEARNING_RATE_AUDIO = 0.001
NUM_EPOCHS_BERT = 5
NUM_EPOCHS_AUDIO = 10
NUM_EPOCHS_zIMAGE = 5

# Audio processing
SAMPLE_RATE = 22050
MFCC_FEATURES = 13
SPECTROGRAM_SIZE = (224, 224)

# Image processing
IMAGE_SIZE = 224
IMAGE_CHANNELS = 3

# Reinforcement Learning
DQN_STATE_SIZE = 256
DQN_ACTION_SIZE = 67  # Number of drugs in expanded recommendation pool
LEARNING_RATE_DQN = 0.001
DISCOUNT_FACTOR = 0.95
EPSILON = 1.0
EPSILON_DECAY = 0.995
EPSILON_MIN = 0.01
MEMORY_SIZE = 1000
BATCH_SIZE_DQN = 32

# Fusion weights
WEIGHT_TEXT = 0.4
WEIGHT_AUDIO = 0.35
WEIGHT_IMAGE = 0.25

# Dataset sizes
TEXT_DATASET_SIZE = 161297
AUDIO_DATASET_SIZE = 1440
IMAGE_DATASET_SIZE = 5000

# Sentiment classes
SENTIMENT_CLASSES = {0: "Negative", 1: "Neutral", 2: "Positive"}
EMOTION_CLASSES = {0: "angry", 1: "disgust", 2: "fear", 3: "happy", 4: "neutral", 5: "sad", 6: "surprise"}
DRUG_VALIDITY_CLASSES = {0: "invalid", 1: "expired", 2: "valid"}

# System configuration
CONFIDENCE_THRESHOLD = 0.15
TOP_K_RECOMMENDATIONS = 5

# Data paths
DATA_PATH = "./data"
MODEL_PATH = "./models"
CHECKPOINT_PATH = "./checkpoints"

# Logging
LOG_LEVEL = "INFO"

import os
import secrets
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///instance/sedrs.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
    JSON_SORT_KEYS = False
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'wav', 'mp3', 'jpg', 'jpeg', 'png', 'gif'}
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_urlsafe(32)
    PERMANENT_SESSION_LIFETIME = 24 * 60 * 60
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Model Config (from global variables)
    BERT_MODEL = BERT_MODEL
    WEIGHT_TEXT = WEIGHT_TEXT
    WEIGHT_AUDIO = WEIGHT_AUDIO
    WEIGHT_IMAGE = WEIGHT_IMAGE

"""Main System Orchestrator - SEDRS (Sentiment-Enhanced Drug Recommendation System)"""

import torch
import numpy as np
import json
from datetime import datetime
import logging

from text_sentiment import TextSentimentAnalyzer
from audio_processing import AudioEmotionAnalyzer
from image_processing import ImageDrugAnalyzer
from fusion import MultiModalFusion
from dqn_rl import DQNAgent
from recommendation_engine import RecommendationEngine
from chatbot import MedicalChatbot, ConversationManager
from data_utils import DataGenerator, MetricsCalculator

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SEDRSystem:
    """Sentiment-Enhanced Drug Recommendation System"""
    
    def __init__(self, device='cpu'):
        """Initialize SEDRS system"""
        self.device = device
        logger.info(f"Initializing SEDRS on device: {device}")
        
        # Initialize models
        self.text_analyzer = TextSentimentAnalyzer(device=device)
        self.audio_analyzer = AudioEmotionAnalyzer(device=device)
        self.image_analyzer = ImageDrugAnalyzer(device=device)
        
        # Fusion mechanism
        self.fusion = MultiModalFusion()
        
        # DQN Agent
        self.dqn_agent = DQNAgent(device=device)
        
        # Recommendation engine
        self.recommendation_engine = RecommendationEngine()
        
        # Chatbot
        self.conversation_manager = ConversationManager()
        
        # System statistics
        self.system_stats = {
            'total_interactions': 0,
            'successful_recommendations': 0,
            'average_confidence': 0.0,
            'interaction_history': []
        }
        
        logger.info("SEDRS system initialized successfully")
    
    def analyze_single_modality(self, modality_type, input_data):
        """
        Analyze single modality input
        
        Args:
            modality_type: 'text', 'audio', or 'image'
            input_data: path or content to analyze
        
        Returns:
            prediction and confidence (as native Python types)
        """
        def _to_python(val):
            """Convert numpy types to native Python types for JSON safety"""
            if hasattr(val, 'item'):
                return val.item()
            return val

        if modality_type == 'text':
            texts = [input_data] if isinstance(input_data, str) else input_data
            predictions, confidences = self.text_analyzer.predict(texts)
            return _to_python(predictions[0]), _to_python(confidences[0])
        
        elif modality_type == 'audio':
            audio_paths = [input_data] if isinstance(input_data, str) else input_data
            predictions, confidences = self.audio_analyzer.predict(audio_paths)
            return _to_python(predictions[0]), _to_python(confidences[0])
        
        elif modality_type == 'image':
            image_paths = [input_data] if isinstance(input_data, str) else input_data
            predictions, confidences = self.image_analyzer.predict(image_paths)
            return _to_python(predictions[0]), _to_python(confidences[0])
        
        else:
            raise ValueError(f"Unknown modality: {modality_type}")
    
    def analyze_multi_modal(self, text_input=None, audio_input=None, image_input=None):
        """
        Perform multi-modal sentiment analysis
        
        Args:
            text_input: patient review text
            audio_input: audio file path
            image_input: drug image path
        
        Returns:
            fused sentiment score and confidence
        """
        results = {
            'text': {'prediction': None, 'confidence': 0.0},
            'audio': {'prediction': None, 'confidence': 0.0},
            'image': {'prediction': None, 'confidence': 0.0}
        }
        
        # Analyze each modality
        if text_input:
            pred, conf = self.analyze_single_modality('text', text_input)
            results['text']['prediction'] = pred
            results['text']['confidence'] = conf
        
        if audio_input:
            pred, conf = self.analyze_single_modality('audio', audio_input)
            results['audio']['prediction'] = pred
            results['audio']['confidence'] = conf
        
        if image_input:
            pred, conf = self.analyze_single_modality('image', image_input)
            results['image']['prediction'] = pred
            results['image']['confidence'] = conf
        
        # Fusion
        text_pred = results['text']['prediction'] or 1
        text_conf = results['text']['confidence'] or 0.5
        audio_pred = results['audio']['prediction'] or 4  # neutral
        audio_conf = results['audio']['confidence'] or 0.5
        image_pred = results['image']['prediction'] or 2  # valid
        image_conf = results['image']['confidence'] or 0.5
        
        fused_score, overall_confidence = self.fusion.fuse_sentiments(
            text_pred, text_conf, audio_pred, audio_conf, image_pred, image_conf
        )
        
        results['fused_sentiment_score'] = float(fused_score)
        results['overall_confidence'] = float(overall_confidence)
        results['individual_results'] = results
        
        return results
    
    def get_recommendations(self, patient_condition, sentiment_results, top_k=5):
        """
        Generate drug recommendations based on sentiment analysis
        
        Args:
            patient_condition: medical condition
            sentiment_results: output from analyze_multi_modal
            top_k: number of recommendations
        
        Returns:
            list of recommended drugs
        """
        sentiment_score = sentiment_results.get('fused_sentiment_score', 1.0)
        confidence = sentiment_results.get('overall_confidence', 0.5)
        
        recommendations = self.recommendation_engine.recommend(
            patient_condition, sentiment_score, confidence, top_k=top_k
        )
        
        return recommendations
    
    def apply_reinforcement_learning(self, state, drug_id, reward):
        """
        Apply RL for continuous learning
        
        Args:
            state: patient state vector
            drug_id: recommended drug ID
            reward: feedback reward
        """
        self.dqn_agent.remember(state, drug_id, reward, state, False)
        loss = self.dqn_agent.replay(batch_size=16)
        
        # Save updated model weights to persist learning
        try:
            self.dqn_agent.save_model('models/dqn_agent.pth')
            logger.info(f"RL Agent updated and saved. Loss: {loss:.4f}")
        except Exception as e:
            logger.error(f"Failed to save RL agent: {e}")
            
        return loss
    
    def full_pipeline(self, patient_condition, text_review=None, audio_path=None, image_path=None, top_k=5):
        """
        Complete drug recommendation pipeline
        
        Args:
            patient_condition: medical condition
            text_review: patient text review
            audio_path: audio feedback path
            image_path: drug image path
        
        Returns:
            recommendations with detailed report
        """
        logger.info(f"Starting full pipeline for condition: {patient_condition}")
        
        # Step 1: Multi-modal analysis
        sentiment_results = self.analyze_multi_modal(text_review, audio_path, image_path)
        
        # Step 2: Get recommendations
        recommendations = self.get_recommendations(patient_condition, sentiment_results, top_k=top_k)
        
        # Step 3: Create report
        report = {
            'timestamp': datetime.now().isoformat(),
            'patient_condition': patient_condition,
            'sentiment_analysis': sentiment_results,
            'recommendations': recommendations,
            'top_recommendation': recommendations[0] if recommendations else None
        }
        
        # Update system stats
        self.system_stats['total_interactions'] += 1
        self.system_stats['successful_recommendations'] += 1 if recommendations else 0
        self.system_stats['interaction_history'].append(report)
        
        logger.info(f"Pipeline completed with {len(recommendations)} recommendations")
        
        return report
    
    def train_models(self, text_data=None, audio_data=None, image_data=None):
        """Train all models"""
        logger.info("Starting model training")
        
        # Generate synthetic data if not provided
        if text_data is None:
            text_data = DataGenerator.generate_text_reviews(num_samples=100)
        
        # Train text model
        if text_data:
            texts, labels = text_data
            logger.info(f"Training text model on {len(texts)} samples")
            self.text_analyzer.train(texts, labels)
        
        # Train audio model (would require audio files)
        logger.info("Audio model training requires audio data")
        
        # Train image model (would require image files)
        logger.info("Image model training requires image data")
        
        # Train RL agent
        logger.info("Training DQN agent")
        for episode in range(20):
            initial_state = np.random.randn(256)
            reward = self.dqn_agent.train_episode(initial_state)
            if (episode + 1) % 5 == 0:
                logger.info(f"DQN Episode {episode+1}/20 - Reward: {reward:.4f}")
        
        logger.info("Model training completed")
    
    def evaluate_system(self, test_data):
        """
        Evaluate system performance
        
        Args:
            test_data: test dataset
        
        Returns:
            evaluation metrics
        """
        logger.info("Starting system evaluation")
        
        predictions = []
        targets = []
        
        for sample in test_data:
            text = sample.get('text')
            label = sample.get('label')
            
            if text:
                pred, _ = self.analyze_single_modality('text', text)
                predictions.append(pred)
                targets.append(label)
        
        if predictions:
            accuracy = MetricsCalculator.calculate_accuracy(
                np.array(predictions), np.array(targets)
            )
            
            metrics = {
                'accuracy': accuracy,
                'total_samples': len(predictions),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Evaluation complete - Accuracy: {accuracy:.4f}")
            return metrics
        
        return None
    
    def get_system_status(self):
        """Get system status and statistics"""
        status = {
            'status': 'operational',
            'timestamp': datetime.now().isoformat(),
            'device': self.device,
            'statistics': self.system_stats,
            'models': {
                'text_analyzer': 'ready',
                'audio_analyzer': 'ready',
                'image_analyzer': 'ready',
                'dqn_agent': 'ready'
            }
        }
        
        return status
    
    def save_system(self, path_prefix='./models/'):
        """Save all models"""
        try:
            self.text_analyzer.save_model(f'{path_prefix}text_model.pth')
            self.audio_analyzer.save_model(f'{path_prefix}audio_model.pth')
            self.image_analyzer.save_model(f'{path_prefix}image_model.pth')
            self.dqn_agent.save_model(f'{path_prefix}dqn_model.pth')
            logger.info("All models saved successfully")
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def load_system(self, path_prefix='./models/'):
        """Load all models"""
        try:
            self.text_analyzer.load_model(f'{path_prefix}text_model.pth')
            self.audio_analyzer.load_model(f'{path_prefix}audio_model.pth')
            self.image_analyzer.load_model(f'{path_prefix}image_model.pth')
            self.dqn_agent.load_model(f'{path_prefix}dqn_model.pth')
            logger.info("All models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading models: {e}")

def main():
    """Main execution function"""
    logger.info("=" * 80)
    logger.info("SEDRS - Sentiment-Enhanced Drug Recommendation System")
    logger.info("=" * 80)
    
    # Determine device
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"Using device: {device}")
    
    # Initialize system
    system = SEDRSystem(device=device)
    
    # Train models
    logger.info("\n" + "=" * 80)
    logger.info("STEP 1: Training Models")
    logger.info("=" * 80)
    system.train_models()
    
    # Run full pipeline with sample data
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: Testing Full Pipeline")
    logger.info("=" * 80)
    
    sample_reviews = [
        "This medication worked amazingly well for my pain relief!",
        "Not very effective, still experiencing symptoms",
        "Average results, nothing special"
    ]
    
    for review in sample_reviews:
        logger.info(f"\nProcessing review: {review}")
        report = system.full_pipeline(
            patient_condition="pain relief",
            text_review=review
        )
        
        recommendations = report.get('recommendations', [])
        if recommendations:
            logger.info(f"Top recommendation: {recommendations[0]['drug_name']}")
            logger.info(f"Recommendation score: {recommendations[0]['score']:.4f}")
    
    # Get system status
    logger.info("\n" + "=" * 80)
    logger.info("STEP 3: System Status")
    logger.info("=" * 80)
    status = system.get_system_status()
    logger.info(f"Total interactions: {status['statistics']['total_interactions']}")
    logger.info(f"Successful recommendations: {status['statistics']['successful_recommendations']}")
    
    # Save results
    logger.info("\n" + "=" * 80)
    logger.info("STEP 4: Saving Results")
    logger.info("=" * 80)
    
    try:
        import os
        os.makedirs('./models/', exist_ok=True)
        system.save_system()
        
        # Save status report
        with open('./models/system_status.json', 'w') as f:
            json.dump(status, f, indent=2, default=str)
        
        logger.info("Results saved successfully")
    except Exception as e:
        logger.error(f"Error saving results: {e}")
    
    logger.info("\n" + "=" * 80)
    logger.info("SEDRS System Execution Complete")
    logger.info("=" * 80)
    
    return system

if __name__ == "__main__":
    system = main()

"""Data Utilities and Preprocessing"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
import json

class DataProcessor:
    """Data preprocessing and utilities"""
    
    @staticmethod
    def split_dataset(X, y, test_size=0.15, val_size=0.15, random_state=42):
        """
        Split dataset into train, validation, and test sets
        Default: 70% train, 15% val, 15% test
        """
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y, test_size=(test_size + val_size), random_state=random_state
        )
        
        val_ratio = val_size / (test_size + val_size)
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=test_size/(test_size + val_size), 
            random_state=random_state
        )
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    @staticmethod
    def normalize_features(X_train, X_val=None, X_test=None):
        """
        Normalize features using StandardScaler
        """
        scaler = StandardScaler()
        X_train_normalized = scaler.fit_transform(X_train)
        
        results = {'scaler': scaler, 'X_train': X_train_normalized}
        
        if X_val is not None:
            results['X_val'] = scaler.transform(X_val)
        if X_test is not None:
            results['X_test'] = scaler.transform(X_test)
        
        return results
    
    @staticmethod
    def encode_labels(y_train, y_val=None, y_test=None):
        """Encode categorical labels"""
        le = LabelEncoder()
        y_train_encoded = le.fit_transform(y_train)
        
        results = {'encoder': le, 'y_train': y_train_encoded}
        
        if y_val is not None:
            results['y_val'] = le.transform(y_val)
        if y_test is not None:
            results['y_test'] = le.transform(y_test)
        
        return results

class DataGenerator:
    """Generate synthetic data for testing and development"""
    
    @staticmethod
    def generate_text_reviews(num_samples=100):
        """Generate synthetic text reviews"""
        positive_reviews = [
            "This medicine worked great for my pain!",
            "Excellent results, highly recommend.",
            "Much better after taking this medication.",
            "Very effective, no side effects!",
            "Best medicine I've ever taken.",
            "Feeling much better now, thank you!",
            "This drug really helped my condition.",
            "Amazing relief from symptoms!",
        ]
        
        negative_reviews = [
            "This medicine didn't work at all.",
            "Terrible side effects, very disappointed.",
            "Made my condition worse.",
            "Waste of money, ineffective.",
            "Strong negative reaction.",
            "Not recommended, causes more problems.",
            "Very poor quality medication.",
            "Extremely disappointed with results.",
        ]
        
        neutral_reviews = [
            "The medicine is okay, nothing special.",
            "Some improvement, but not significant.",
            "Average results, nothing remarkable.",
            "Somewhat helpful, could be better.",
            "Neither good nor bad experience.",
            "Limited effectiveness observed.",
        ]
        
        reviews = []
        labels = []
        
        samples_per_class = num_samples // 3
        
        for _ in range(samples_per_class):
            reviews.append(np.random.choice(positive_reviews))
            labels.append(2)  # Positive
        
        for _ in range(samples_per_class):
            reviews.append(np.random.choice(negative_reviews))
            labels.append(0)  # Negative
        
        for _ in range(samples_per_class):
            reviews.append(np.random.choice(neutral_reviews))
            labels.append(1)  # Neutral
        
        return reviews, labels
    
    @staticmethod
    def generate_synthetic_features(num_samples=100, feature_dim=256):
        """Generate synthetic feature vectors"""
        features = np.random.randn(num_samples, feature_dim).astype(np.float32)
        labels = np.random.randint(0, 3, num_samples)
        
        return features, labels
    
    @staticmethod
    def generate_rl_states(num_episodes=100, state_dim=256):
        """Generate synthetic RL states"""
        episodes = []
        
        for _ in range(num_episodes):
            state = np.random.randn(state_dim).astype(np.float32)
            action = np.random.randint(0, 50)
            reward = np.random.randn()
            next_state = state + np.random.randn(state_dim) * 0.1
            done = np.random.random() < 0.1
            
            episodes.append({
                'state': state,
                'action': action,
                'reward': reward,
                'next_state': next_state,
                'done': done
            })
        
        return episodes

class MetricsCalculator:
    """Calculate evaluation metrics"""
    
    @staticmethod
    def calculate_accuracy(predictions, targets):
        """Calculate accuracy"""
        return np.mean(predictions == targets)
    
    @staticmethod
    def calculate_precision(predictions, targets, class_id):
        """Calculate precision for a class"""
        true_positives = np.sum((predictions == class_id) & (targets == class_id))
        predicted_positives = np.sum(predictions == class_id)
        
        if predicted_positives == 0:
            return 0
        
        return true_positives / predicted_positives
    
    @staticmethod
    def calculate_recall(predictions, targets, class_id):
        """Calculate recall for a class"""
        true_positives = np.sum((predictions == class_id) & (targets == class_id))
        actual_positives = np.sum(targets == class_id)
        
        if actual_positives == 0:
            return 0
        
        return true_positives / actual_positives
    
    @staticmethod
    def calculate_f1_score(precision, recall):
        """Calculate F1 score"""
        if precision + recall == 0:
            return 0
        
        return 2 * (precision * recall) / (precision + recall)
    
    @staticmethod
    def create_confusion_matrix(predictions, targets, num_classes):
        """Create confusion matrix"""
        matrix = np.zeros((num_classes, num_classes))
        
        for pred, target in zip(predictions, targets):
            matrix[target, pred] += 1
        
        return matrix

class ResultsExporter:
    """Export results and reports"""
    
    @staticmethod
    def export_metrics_to_json(metrics, filepath):
        """Export metrics to JSON"""
        with open(filepath, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
    
    @staticmethod
    def export_to_csv(data, filepath):
        """Export data to CSV"""
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
    
    @staticmethod
    def create_report(model_name, metrics, test_size=None):
        """Create evaluation report"""
        report = {
            'model_name': model_name,
            'timestamp': pd.Timestamp.now().isoformat(),
            'metrics': metrics,
            'test_size': test_size
        }
        
        return report

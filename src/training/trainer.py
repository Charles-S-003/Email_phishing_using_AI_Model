import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from src.models.ensemble_model import EnsemblePhishingDetector

class PhishingDetectionTrainer:
    def prepare_dataset(self, data_path):
        """Prepare dataset for training."""
        try:
            # Generate synthetic training data
            n_samples = 200
            np.random.seed(42)
            
            features = np.random.rand(n_samples, 4)  # 4 features
            labels = np.random.randint(0, 2, n_samples)  # Binary labels
            
            return features, labels, None
            
        except Exception as e:
            print(f"Error preparing dataset: {str(e)}")
            return np.array([]), np.array([]), None

    def train_model(self, features, labels):
        """Train the model and return results."""
        if len(features) == 0 or len(labels) == 0:
            return {'accuracy': 0, 'model': None}

        # Split dataset
        X_train, X_test, y_train, y_test = train_test_split(
            features, labels, test_size=0.2, random_state=42
        )
        
        # Initialize and train model
        model = EnsemblePhishingDetector(random_state=42)
        model.fit(X_train, y_train)
        
        accuracy = model.model.score(X_test, y_test)
        print(f"Model training completed. Accuracy: {accuracy:.2%}")
        
        return {
            'accuracy': accuracy,
            'model': model
        }
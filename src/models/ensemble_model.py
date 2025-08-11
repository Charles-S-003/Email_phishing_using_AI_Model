from sklearn.ensemble import RandomForestClassifier
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin

class EnsemblePhishingDetector(BaseEstimator, ClassifierMixin):
    def __init__(self, random_state=42):
        self.random_state = random_state
        self.model = RandomForestClassifier(
            n_estimators=100,
            min_samples_leaf=5,
            random_state=random_state
        )
        self.is_fitted = False
        self.feature_names = ['text_length', 'urls_count', 
                            'has_urgency_words', 'has_suspicious_links']
    
    def fit(self, X, y):
        """Train the model on input data."""
        if X.shape[0] == 0 or len(y) == 0:
            raise ValueError("Empty training data")
        
        self.model.fit(X, y)
        self.is_fitted = True
        return self
    
    def predict(self, features):
        """Make predictions on new data."""
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        X = self._prepare_features(features)
        return self.model.predict(X)
    
    def predict_proba(self, features):
        """Get prediction probabilities."""
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        X = self._prepare_features(features)
        return self.model.predict_proba(X)
    
    def _prepare_features(self, features):
        """Convert features to proper numpy array format."""
        if isinstance(features, dict):
            return np.array([[features.get(f, 0) for f in self.feature_names]])
        return np.asarray(features)

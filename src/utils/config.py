import yaml
import os
from pathlib import Path

class Config:
    def __init__(self, config_path="config/config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
            return config
        except FileNotFoundError:
            print(f"Config file {self.config_path} not found. Using defaults.")
            return self.get_default_config()
    
    def get_default_config(self):
        """Return default configuration"""
        return {
            'data': {
                'raw_data_path': 'data/raw/',
                'processed_data_path': 'data/processed/',
                'batch_size': 1000,
                'test_split': 0.2,
                'validation_split': 0.2
            },
            'features': {
                'max_tfidf_features': 5000,
                'max_count_features': 1000,
                'ngram_range': [1, 3],
                'min_df': 2,
                'max_df': 0.95
            },
            'models': {
                'random_state': 42,
                'cv_folds': 5,
                'ensemble_method': 'stacking'
            },
            'training': {
                'epochs': 50,
                'learning_rate': 0.001,
                'patience': 10,
                'batch_size': 32
            },
            'api': {
                'host': '0.0.0.0',
                'port': 5000,
                'debug': False
            }
        }
    
    def get(self, key, default=None):
        """Get configuration value by key"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            value = value.get(k, {})
        return value if value != {} else default

# Global config instance
config = Config()

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.preprocessing import StandardScaler, LabelEncoder
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import re
from src.utils.logger import setup_logger
from src.utils.config import config

logger = setup_logger(__name__)

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except:
    logger.warning("Could not download NLTK data")

class FeatureExtractor:
    def __init__(self):
        self.tfidf_vectorizer = None
        self.count_vectorizer = None
        self.scaler = StandardScaler()
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english')) if nltk.data.find('corpora/stopwords') else set()
        
        # Feature configurations
        self.max_features = config.get('features.max_tfidf_features', 5000)
        self.ngram_range = tuple(config.get('features.ngram_range', [1, 3]))
        self.min_df = config.get('features.min_df', 2)
        self.max_df = config.get('features.max_df', 0.95)
    
    def extract_all_features(self, email_data):
        """Extract all features from parsed email data"""
        logger.info("Extracting comprehensive feature set...")
        
        if isinstance(email_data, pd.DataFrame):
            features_list = []
            for idx, row in email_data.iterrows():
                features = self._extract_single_email_features(row)
                features_list.append(features)
            
            features_df = pd.DataFrame(features_list)
        else:
            # Single email
            features = self._extract_single_email_features(email_data)
            features_df = pd.DataFrame([features])
        
        return features_df
    
    def _extract_single_email_features(self, email_row):
        """Extract features from a single email"""
        features = {}
        
        # Get parsed components
        if hasattr(email_row, 'features') and email_row.features:
            features.update(email_row.features)
        
        # Text-based features
        body = getattr(email_row, 'body', '') or ''
        subject = getattr(email_row, 'subject', '') or ''
        
        # Combine text content
        combined_text = f"{subject} {body}"
        
        # Statistical features
        features.update(self._extract_statistical_features(combined_text, subject, body))
        
        # Linguistic features
        features.update(self._extract_linguistic_features(combined_text))
        
        # Metadata features
        if hasattr(email_row, 'headers'):
            features.update(self._extract_metadata_features(email_row.headers))
        
        # Sender features
        if hasattr(email_row, 'sender'):
            features.update(self._extract_sender_features(email_row.sender))
        
        return features
    
    def _extract_statistical_features(self, text, subject, body):
        """Extract statistical text features"""
        features = {}
        
        # Length features
        features['total_length'] = len(text)
        features['subject_length'] = len(subject)
        features['body_length'] = len(body)
        features['avg_word_length'] = np.mean([len(word) for word in text.split()]) if text.split() else 0
        
        # Character distribution
        features['alpha_ratio'] = sum(c.isalpha() for c in text) / len(text) if text else 0
        features['digit_ratio'] = sum(c.isdigit() for c in text) / len(text) if text else 0
        features['space_ratio'] = sum(c.isspace() for c in text) / len(text) if text else 0
        features['punct_ratio'] = sum(c in '.,!?;:' for c in text) / len(text) if text else 0
        
        # Sentence features
        sentences = text.split('.')
        features['sentence_count'] = len(sentences)
        features['avg_sentence_length'] = np.mean([len(s.split()) for s in sentences if s.strip()]) if sentences else 0
        
        # Word frequency features
        words = text.lower().split()
        if words:
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            features['unique_word_ratio'] = len(set(words)) / len(words)
            features['max_word_freq'] = max(word_freq.values())
            features['avg_word_freq'] = np.mean(list(word_freq.values()))
        else:
            features['unique_word_ratio'] = 0
            features['max_word_freq'] = 0
            features['avg_word_freq'] = 0
        
        return features
    
    def _extract_linguistic_features(self, text):
        """Extract linguistic features"""
        features = {}
        
        # POS tagging features (simplified)
        words = word_tokenize(text.lower()) if text else []
        
        # Function words ratio
        function_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        features['function_word_ratio'] = sum(1 for word in words if word in function_words) / len(words) if words else 0
        
        # Lexical diversity
        features['lexical_diversity'] = len(set(words)) / len(words) if words else 0
        
        # Readability features (simplified)
        sentences = text.split('.')
        features['avg_words_per_sentence'] = len(words) / len(sentences) if sentences else 0
        
        # Complex words (>6 characters)
        complex_words = [word for word in words if len(word) > 6]
        features['complex_word_ratio'] = len(complex_words) / len(words) if words else 0
        
        return features
    
    def _extract_metadata_features(self, headers):
        """Extract metadata features from email headers"""
        features = {}
        
        if not headers:
            return features
        
        # Header completeness
        required_headers = ['From', 'To', 'Subject', 'Date']
        features['header_completeness'] = sum(1 for h in required_headers if h in headers) / len(required_headers)
        
        # Authentication indicators
        auth_headers = ['DKIM-Signature', 'Authentication-Results', 'SPF', 'DMARC']
        features['auth_header_count'] = sum(1 for h in auth_headers if h in headers)
        
        # Received headers count (indicates routing path)
        if 'Received' in headers:
            if isinstance(headers['Received'], list):
                features['received_count'] = len(headers['Received'])
            else:
                features['received_count'] = 1
        else:
            features['received_count'] = 0
        
        return features
    
    def _extract_sender_features(self, sender):
        """Extract features from the sender's email address"""
        features = {}
        
        # Basic sender features
        features['sender_domain'] = sender.split('@')[1] if '@' in sender else ''
        features['has_valid_domain'] = any(domain in sender for domain in ['gmail.com', 'yahoo.com', 'hotmail.com'])
        
        return features
    
    def create_text_features(self, texts, fit=True):
        """Create TF-IDF and Count vectorizer features"""
        logger.info("Creating text vectorization features...")
        
        # Preprocess texts
        processed_texts = [self.preprocess_text(text) for text in texts]
        
        if fit:
            # Fit vectorizers
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=self.max_features,
                ngram_range=self.ngram_range,
                min_df=self.min_df,
                max_df=self.max_df,
                stop_words='english'
            )
            
            self.count_vectorizer = CountVectorizer(
                max_features=config.get('features.max_count_features', 1000),
                ngram_range=(1, 2),
                min_df=self.min_df,
                max_df=self.max_df,
                stop_words='english'
            )
            
            tfidf_features = self.tfidf_vectorizer.fit_transform(processed_texts)
            count_features = self.count_vectorizer.fit_transform(processed_texts)
        else:
            # Transform using existing vectorizers
            tfidf_features = self.tfidf_vectorizer.transform(processed_texts)
            count_features = self.count_vectorizer.transform(processed_texts)
        
        return tfidf_features, count_features
    
    def preprocess_text(self, text):
        """Preprocess text for vectorization"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Tokenize and remove stopwords
        words = word_tokenize(text)
        words = [word for word in words if word not in self.stop_words and len(word) > 2]
        
        # Stem words
        words = [self.stemmer.stem(word) for word in words]
        
        return ' '.join(words)
    
    def scale_features(self, features, fit=True):
        """Scale numerical features"""
        if fit:
            return self.scaler.fit_transform(features)
        else:
            return self.scaler.transform(features)

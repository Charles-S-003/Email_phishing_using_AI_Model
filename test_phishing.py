from src.data_collection.email_collector import EmailDataCollector
from src.data_preprocessing.email_parser import EmailParser
from src.features.feature_extractor import FeatureExtractor
from src.models.ensemble_model import EnsemblePhishingDetector
from src.training.trainer import PhishingDetectionTrainer
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    # 1. Generate sample data
    logger.info("Generating sample email data...")
    collector = EmailDataCollector()
    emails_df = collector.generate_sample_emails(n_phishing=100, n_legitimate=100)
    
    # 2. Initialize trainer
    trainer = PhishingDetectionTrainer()
    
    # 3. Prepare dataset
    logger.info("Preparing dataset...")
    features, labels, _ = trainer.prepare_dataset(None)
    
    # 4. Train model
    logger.info("Training model...")
    results = trainer.train_model(features, labels)
    model = results['model']
    
    # Test prediction with properly formatted features
    sample_features = {
        'text_length': 150,
        'urls_count': 2,
        'has_urgency_words': 1,
        'has_suspicious_links': 1
    }
    
    if model is not None and model.is_fitted:
        prediction = model.predict(sample_features)
        probability = model.predict_proba(sample_features)
        
        logger.info(f"Sample Email Prediction: {'Phishing' if prediction[0] == 1 else 'Legitimate'}")
        logger.info(f"Confidence: {probability[0][1]:.2%}")
    else:
        logger.error("Model training failed")

if __name__ == "__main__":
    main()
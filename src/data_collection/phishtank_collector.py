import requests
import pandas as pd
import json
import time
from datetime import datetime
import os
from bs4 import BeautifulSoup
from src.utils.logger import setup_logger
from src.utils.config import config

logger = setup_logger(__name__)

class PhishTankCollector:
    def __init__(self, api_key=None):
        self.api_key = api_key or config.get('data.phishtank_api_key')
        self.base_url = "http://data.phishtank.com/data/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def collect_verified_phishes(self, save_path="data/raw/phishtank/"):
        """Collect verified phishing URLs from PhishTank"""
        logger.info("Starting PhishTank data collection...")
        
        os.makedirs(save_path, exist_ok=True)
        
        try:
            # Get verified online phishes
            online_url = f"{self.base_url}{self.api_key}/online_valid.csv" if self.api_key else \
                        "http://data.phishtank.com/data/online_valid.csv"
            
            logger.info(f"Fetching data from: {online_url}")
            response = self.session.get(online_url, timeout=30)
            
            if response.status_code == 200:
                # Save raw CSV
                with open(os.path.join(save_path, "verified_online.csv"), 'wb') as f:
                    f.write(response.content)
                
                # Load and process
                df = pd.read_csv(os.path.join(save_path, "verified_online.csv"))
                logger.info(f"Collected {len(df)} verified phishing URLs")
                
                # Add metadata
                df['collection_date'] = datetime.now().isoformat()
                df['source'] = 'phishtank_verified'
                
                # Save processed data
                df.to_csv(os.path.join(save_path, "processed_phishtank.csv"), index=False)
                
                return df
            else:
                logger.error(f"Failed to fetch PhishTank data: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error collecting PhishTank data: {str(e)}")
            return None
    
    def collect_recent_submissions(self, save_path="data/raw/phishtank/"):
        """Collect recent submissions from PhishTank"""
        logger.info("Collecting recent PhishTank submissions...")
        
        try:
            url = "https://www.phishtank.com/"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find the recent submissions table
                submissions = []
                tables = soup.find_all('table')
                
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows[1:]:  # Skip header
                        cols = row.find_all('td')
                        if len(cols) >= 3:
                            try:
                                submission = {
                                    'phish_id': cols[0].get_text(strip=True),
                                    'url': cols[1].get_text(strip=True),
                                    'submitted_by': cols[2].get_text(strip=True),
                                    'submission_time': datetime.now().isoformat(),
                                    'source': 'phishtank_recent'
                                }
                                submissions.append(submission)
                            except Exception as e:
                                logger.warning(f"Error parsing row: {e}")
                                continue
                
                if submissions:
                    df = pd.DataFrame(submissions)
                    os.makedirs(save_path, exist_ok=True)
                    df.to_csv(os.path.join(save_path, "recent_submissions.csv"), index=False)
                    logger.info(f"Collected {len(submissions)} recent submissions")
                    return df
                else:
                    logger.warning("No recent submissions found")
                    return pd.DataFrame()
                    
        except Exception as e:
            logger.error(f"Error collecting recent submissions: {str(e)}")
            return pd.DataFrame()
    
    def generate_sample_data(self, n_samples=1000, save_path="data/raw/"):
        """Generate sample dataset for testing when API is not available"""
        logger.info(f"Generating {n_samples} sample phishing URLs...")
        
        # Sample phishing URL patterns
        phishing_patterns = [
            "https://secure-{bank}.{tld}/login",
            "https://{bank}-verify.{tld}/account", 
            "https://update-{service}.{tld}/confirm",
            "https://{service}-security.{tld}/verify",
            "https://confirm-{bank}.{suspicious_tld}/update"
        ]
        
        banks = ['paypal', 'amazon', 'microsoft', 'apple', 'google', 'facebook', 'netflix']
        services = ['paypal', 'amazon', 'microsoft', 'apple', 'google', 'dropbox', 'netflix']
        tlds = ['com', 'net', 'org']
        suspicious_tlds = ['tk', 'ml', 'ga', 'cf', 'info', 'biz']
        
        import random
        random.seed(42)
        
        sample_data = []
        for i in range(n_samples):
            pattern = random.choice(phishing_patterns)
            url = pattern.format(
                bank=random.choice(banks),
                service=random.choice(services),
                tld=random.choice(tlds + suspicious_tlds),
                suspicious_tld=random.choice(suspicious_tlds)
            )
            
            sample_data.append({
                'phish_id': f"sample_{i+1}",
                'url': url,
                'phish_detail_url': f"https://www.phishtank.com/phish_detail.php?phish_id=sample_{i+1}",
                'submission_time': datetime.now().isoformat(),
                'verified': 'yes',
                'verification_time': datetime.now().isoformat(),
                'online': 'yes',
                'target': random.choice(banks + services),
                'source': 'generated_sample'
            })
        
        df = pd.DataFrame(sample_data)
        os.makedirs(save_path, exist_ok=True)
        df.to_csv(os.path.join(save_path, "sample_phishing_data.csv"), index=False)
        
        logger.info(f"Generated {len(sample_data)} sample records")
        return df

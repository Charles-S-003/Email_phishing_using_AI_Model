import os
import email
import pandas as pd
import numpy as np
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
from datetime import datetime, timedelta
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class EmailDataCollector:
    def __init__(self):
        self.phishing_templates = [
            {
                'subject': 'Urgent: Your Account Will Be Suspended',
                'sender': 'security@{fake_domain}',
                'body': '''Dear Customer,
                
Your account security has been compromised. Click here immediately to verify your account:
{phishing_url}

Failure to verify within 24 hours will result in permanent account suspension.

Best regards,
Security Team'''
            },
            {
                'subject': 'Payment Failed - Action Required',
                'sender': 'billing@{fake_domain}',
                'body': '''Hello,

Your recent payment has failed. Please update your payment information:
{phishing_url}

Your account will be suspended if not updated within 48 hours.

Thanks,
Billing Department'''
            },
            {
                'subject': 'Congratulations! You\'ve Won $1000',
                'sender': 'winner@{fake_domain}',
                'body': '''Congratulations!

You have been selected to receive $1000! Click here to claim:
{phishing_url}

This offer expires in 24 hours.

Lottery Commission'''
            }
        ]
        
        self.legitimate_templates = [
            {
                'subject': 'Your Order Confirmation #12345',
                'sender': 'orders@legitstore.com',
                'body': '''Thank you for your order!

Order Details:
- Item: Product Name
- Total: $99.99
- Shipping: 3-5 business days

Track your order: https://legitstore.com/track/12345

Customer Service Team'''
            },
            {
                'subject': 'Weekly Newsletter - Tech Updates',
                'sender': 'newsletter@techcompany.com',
                'body': '''This Week in Tech

- New smartphone releases
- Software updates
- Industry news

Read more: https://techcompany.com/newsletter

Unsubscribe: https://techcompany.com/unsubscribe

Tech Company'''
            }
        ]
        
        self.legitimate_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'company.com']
        self.phishing_domains = ['suspicious.com', 'fake-bank.com', 'scam.net']
    
    def generate_sample_emails(self, n_phishing=500, n_legitimate=500, save_path="data/raw/emails/"):
        """Generate sample email dataset"""
        logger.info(f"Generating {n_phishing} phishing and {n_legitimate} legitimate emails...")
        
        os.makedirs(save_path, exist_ok=True)
        os.makedirs(os.path.join(save_path, "phishing"), exist_ok=True)
        os.makedirs(os.path.join(save_path, "legitimate"), exist_ok=True)
        
        all_emails = []
        
        # Generate phishing emails
        for i in range(n_phishing):
            template = random.choice(self.phishing_templates)
            email_data = self._create_email(template, 'phishing', i)
            all_emails.append(email_data)
            
            # Save individual email file
            with open(os.path.join(save_path, "phishing", f"phishing_{i+1}.eml"), 'w') as f:
                f.write(email_data['raw_email'])
        
        # Generate legitimate emails
        for i in range(n_legitimate):
            template = random.choice(self.legitimate_templates)
            email_data = self._create_email(template, 'legitimate', i)
            all_emails.append(email_data)
            
            # Save individual email file
            with open(os.path.join(save_path, "legitimate", f"legitimate_{i+1}.eml"), 'w') as f:
                f.write(email_data['raw_email'])
        
        # Create DataFrame and save
        df = pd.DataFrame(all_emails)
        df.to_csv(os.path.join(save_path, "email_dataset.csv"), index=False)
        
        logger.info(f"Generated {len(all_emails)} total emails")
        return df
    
    def _create_email(self, template, label, index):
        """Create individual email from template"""
        fake_domains = ['secure-bank.tk', 'verify-account.ml', 'update-info.ga', 'confirm-payment.cf']
        phishing_urls = ['http://malicious-site.tk/login', 'http://fake-bank.ml/verify', 'http://scam-site.ga/update']
        
        # Create email
        msg = MIMEMultipart()
        
        # Fill template
        sender = template['sender'].format(fake_domain=random.choice(fake_domains))
        body = template['body'].format(
            phishing_url=random.choice(phishing_urls) if label == 'phishing' else 'https://legitimate-site.com',
            fake_domain=random.choice(fake_domains)
        )
        
        # Set headers
        msg['Subject'] = template['subject']
        msg['From'] = sender
        msg['To'] = 'user@example.com'
        msg['Date'] = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%a, %d %b %Y %H:%M:%S %z')
        msg['Message-ID'] = f"<{random.randint(100000, 999999)}.{random.randint(100000, 999999)}@example.com>"
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        return {
            'email_id': f"{label}_{index+1}",
            'subject': template['subject'],
            'sender': sender,
            'body': body,
            'label': 1 if label == 'phishing' else 0,
            'raw_email': msg.as_string()
        }
    
    def _generate_legitimate_emails(self, n_samples):
        # Generate sample legitimate emails
        data = []
        for _ in range(n_samples):
            data.append({
                'subject': 'Regular Business Communication',
                'body': 'This is a legitimate email content.',
                'sender': f'user@{np.random.choice(self.legitimate_domains)}',
                'is_phishing': 0
            })
        return pd.DataFrame(data)
    
    def _generate_phishing_emails(self, n_samples):
        # Generate sample phishing emails
        data = []
        for _ in range(n_samples):
            data.append({
                'subject': 'URGENT: Account Verification Required',
                'body': 'Click here to verify your account: http://malicious-link.com',
                'sender': f'security@{np.random.choice(self.phishing_domains)}',
                'is_phishing': 1
            })
        return pd.DataFrame(data)

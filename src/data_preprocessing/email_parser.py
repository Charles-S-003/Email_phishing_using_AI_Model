import email
import re
from email.header import decode_header
from urllib.parse import urlparse
import hashlib
from datetime import datetime
import tldextract
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

try:
    import tldextract
except ImportError:
    print("Warning: tldextract not found. Installing required package...")
    import subprocess
    subprocess.check_call(["pip", "install", "tldextract"])
    import tldextract

class EmailParser:
    def __init__(self):
        self.suspicious_patterns = [
            r'urgent.*action.*required',
            r'click.*here.*immediately', 
            r'verify.*account.*now',
            r'suspended.*account',
            r'limited.*time.*offer',
            r'congratulations.*winner',
            r'claim.*prize.*now',
            r'update.*payment.*info'
        ]
        
        self.suspicious_domains = [
            'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly',
            '.tk', '.ml', '.ga', '.cf', 'tempmail'
        ]
    
    def parse_email(self, email_content):
        """Parse email and extract comprehensive features"""
        try:
            if isinstance(email_content, str):
                msg = email.message_from_string(email_content)
            else:
                msg = email_content
            
            # Extract components
            headers = self.extract_headers(msg)
            body = self.extract_body(msg)
            urls = self.extract_urls(body + str(headers))
            
            # Calculate features
            features = self.calculate_comprehensive_features(headers, body, urls)
            
            return {
                'headers': headers,
                'body': body,
                'urls': urls,
                'features': features,
                'parsed_successfully': True
            }
            
        except Exception as e:
            logger.error(f"Error parsing email: {str(e)}")
            return {
                'headers': {},
                'body': '',
                'urls': [],
                'features': {},
                'parsed_successfully': False
            }
    
    def extract_headers(self, msg):
        """Extract and decode email headers"""
        headers = {}
        
        important_headers = [
            'From', 'To', 'Subject', 'Date', 'Reply-To', 'Return-Path',
            'Message-ID', 'X-Originating-IP', 'Received', 'Content-Type',
            'X-Mailer', 'X-Priority', 'Authentication-Results', 'DKIM-Signature'
        ]
        
        for header in important_headers:
            try:
                if header in msg:
                    value = msg[header]
                    if value:
                        # Decode header if needed
                        if isinstance(value, str):
                            headers[header] = value
                        else:
                            try:
                                decoded = decode_header(value)[0]
                                if decoded[1]:
                                    headers[header] = decoded[0].decode(decoded[1])
                                else:
                                    headers[header] = str(decoded[0])
                            except:
                                headers[header] = str(value)
            except Exception as e:
                logger.warning(f"Error decoding header {header}: {e}")
                continue
        
        return headers
    
    def extract_body(self, msg):
        """Extract email body content"""
        body = ""
        
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            body += payload.decode('utf-8', errors='ignore')
                    elif content_type == "text/html":
                        payload = part.get_payload(decode=True)
                        if payload:
                            html_content = payload.decode('utf-8', errors='ignore')
                            body += self.html_to_text(html_content)
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.warning(f"Error extracting body: {e}")
            body = str(msg.get_payload())
        
        return body
    
    def extract_urls(self, text):
        """Extract URLs from text"""
        # More comprehensive URL regex
        url_patterns = [
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            r'www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}'
        ]
        
        urls = []
        for pattern in url_patterns:
            urls.extend(re.findall(pattern, text, re.IGNORECASE))
        
        # Clean and deduplicate
        cleaned_urls = []
        for url in urls:
            if not url.startswith(('http://', 'https://')):
                if url.startswith('www.'):
                    url = 'http://' + url
                elif '.' in url and len(url) > 4:
                    url = 'http://' + url
            
            if url not in cleaned_urls and len(url) > 4:
                cleaned_urls.append(url)
        
        return cleaned_urls
    
    def calculate_comprehensive_features(self, headers, body, urls):
        """Calculate comprehensive feature set"""
        features = {}
        
        # Header features
        features.update(self._calculate_header_features(headers))
        
        # Content features  
        features.update(self._calculate_content_features(body))
        
        # URL features
        features.update(self._calculate_url_features(urls))
        
        # Behavioral features
        features.update(self._calculate_behavioral_features(headers, body, urls))
        
        return features
    
    def _calculate_header_features(self, headers):
        """Calculate header-based features"""
        features = {}
        
        # Basic header presence
        features['has_reply_to'] = int('Reply-To' in headers)
        features['has_return_path'] = int('Return-Path' in headers)
        features['has_message_id'] = int('Message-ID' in headers)
        features['has_date'] = int('Date' in headers)
        
        # Sender analysis
        sender = headers.get('From', '')
        features['sender_length'] = len(sender)
        features['sender_has_name'] = int('<' in sender and '>' in sender)
        features['sender_domain'] = self.extract_domain(sender)
        features['sender_domain_length'] = len(features['sender_domain'])
        
        # Subject analysis
        subject = headers.get('Subject', '')
        features['subject_length'] = len(subject)
        features['subject_caps_ratio'] = self.caps_ratio(subject)
        features['subject_exclamation_count'] = subject.count('!')
        features['subject_question_count'] = subject.count('?')
        
        # Authentication features
        features['has_dkim'] = int('DKIM-Signature' in headers)
        features['has_auth_results'] = int('Authentication-Results' in headers)
        
        return features
    
    def _calculate_content_features(self, body):
        """Calculate content-based features"""
        features = {}
        
        # Basic statistics
        features['body_length'] = len(body)
        features['word_count'] = len(body.split())
        features['line_count'] = len(body.split('\n'))
        features['paragraph_count'] = len(body.split('\n\n'))
        
        # Character analysis
        features['caps_ratio'] = self.caps_ratio(body)
        features['digit_ratio'] = sum(c.isdigit() for c in body) / len(body) if body else 0
        features['punct_ratio'] = sum(c in '!@#$%^&*().,;:' for c in body) / len(body) if body else 0
        
        # Exclamation and urgency
        features['exclamation_count'] = body.count('!')
        features['question_count'] = body.count('?')
        features['urgency_words'] = self.count_urgency_words(body)
        
        # Suspicious patterns
        features['suspicious_patterns'] = self.count_suspicious_patterns(body)
        
        # Money/financial terms
        features['money_mentions'] = self.count_money_terms(body)
        
        return features
    
    def _calculate_url_features(self, urls):
        """Calculate URL-based features"""
        features = {}
        
        features['url_count'] = len(urls)
        
        if not urls:
            features.update({
                'avg_url_length': 0,
                'shortened_urls': 0,
                'suspicious_domains': 0,
                'unique_domains': 0,
                'ip_addresses': 0,
                'https_ratio': 0
            })
        else:
            # URL statistics
            features['avg_url_length'] = sum(len(url) for url in urls) / len(urls)
            features['shortened_urls'] = sum(1 for url in urls if self.is_shortened_url(url))
            features['suspicious_domains'] = sum(1 for url in urls if self.is_suspicious_domain(url))
            features['ip_addresses'] = sum(1 for url in urls if self.has_ip_address(url))
            features['https_ratio'] = sum(1 for url in urls if url.startswith('https://')) / len(urls)
            
            # Domain analysis
            domains = [self.extract_domain_from_url(url) for url in urls]
            features['unique_domains'] = len(set(domains))
            
        return features
    
    
    def _calculate_behavioral_features(self, headers, body, urls):
        """Calculate behavioral and combined features"""
        features = {}
        
        # Time-based features
        if 'Date' in headers:
            try:
                from email.utils import parsedate_to_datetime
                email_date = parsedate_to_datetime(headers['Date'])
                features['sent_on_weekend'] = int(email_date.weekday() >= 5)
                features['sent_at_night'] = int(email_date.hour < 6 or email_date.hour > 22)
            except:
                features['sent_on_weekend'] = 0
                features['sent_at_night'] = 0
        else:
            features['sent_on_weekend'] = 0
            features['sent_at_night'] = 0
        
        # Sender-subject consistency
        sender_domain = self.extract_domain(headers.get('From', ''))
        subject = headers.get('Subject', '')
        features['sender_subject_mismatch'] = int(
            sender_domain and subject and 
            not any(word in subject.lower() for word in sender_domain.lower().split('.'))
        )
        
        # Content-URL consistency
        features['content_url_ratio'] = len(urls) / max(len(body.split()), 1)
        
        return features
    
    def extract_domain(self, email_address):
        """Extract domain from email address"""
        try:
            if '@' in email_address:
                return email_address.split('@')[-1].strip('>')
            return ''
        except:
            return ''
    
    def extract_domain_from_url(self, url):
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ''
    
    def caps_ratio(self, text):
        """Calculate ratio of capital letters"""
        if not text:
            return 0
        return sum(1 for c in text if c.isupper()) / len(text)
    
    def count_urgency_words(self, text):
        """Count urgency-related words"""
        urgency_words = [
            'urgent', 'immediate', 'act now', 'limited time', 'expires',
            'deadline', 'hurry', 'quick', 'fast', 'soon', 'asap'
        ]
        text_lower = text.lower()
        return sum(1 for word in urgency_words if word in text_lower)
    
    def count_suspicious_patterns(self, text):
        """Count suspicious patterns"""
        text_lower = text.lower()
        count = 0
        for pattern in self.suspicious_patterns:
            if re.search(pattern, text_lower):
                count += 1
        return count
    
    def count_money_terms(self, text):
        """Count money-related terms"""
        money_terms = [
            '$', '€', '£', 'money', 'cash', 'prize', 'winner', 'lottery',
            'million', 'thousand', 'payment', 'credit', 'bank', 'account'
        ]
        text_lower = text.lower()
        return sum(1 for term in money_terms if term in text_lower)
    
    def is_shortened_url(self, url):
        """Check if URL is shortened"""
        shortened_services = ['bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly']
        return any(service in url for service in shortened_services)
    
    def is_suspicious_domain(self, url):
        """Check if domain is suspicious"""
        return any(domain in url for domain in self.suspicious_domains)
    
    def has_ip_address(self, url):
        """Check if URL contains IP address"""
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        return bool(re.search(ip_pattern, url))
    
    def html_to_text(self, html_content):
        """Convert HTML to plain text"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text()
        except:
            # Fallback: simple HTML tag removal
            return re.sub('<[^<]+?>', '', html_content)
    
    def parse_email(self, email_data):
        """Parse email data and extract relevant features."""
        try:
            # Handle both dictionary and string inputs
            if isinstance(email_data, str):
                # If input is string, assume it's the email body
                return self._parse_text_only(email_data)
            else:
                return {
                    'subject': self._clean_text(email_data.get('subject', '')),
                    'body': self._clean_text(email_data.get('body', '')),
                    'sender': email_data.get('sender', '').lower(),
                    'features': {
                        'has_urgency_words': self._check_urgency(email_data.get('subject', '')),
                        'has_suspicious_links': self._check_links(email_data.get('body', '')),
                        'sender_domain': self._extract_sender_domain(email_data.get('sender', ''))
                    }
                }
        except Exception as e:
            print(f"Error parsing email: {str(e)}")
            # Return default values instead of None
            return {
                'subject': '',
                'body': '',
                'sender': '',
                'features': {
                    'has_urgency_words': False,
                    'has_suspicious_links': False,
                    'sender_domain': ''
                }
            }

    def _parse_text_only(self, text):
        """Handle text-only input."""
        return {
            'subject': '',
            'body': self._clean_text(text),
            'sender': '',
            'features': {
                'has_urgency_words': self._check_urgency(text),
                'has_suspicious_links': self._check_links(text),
                'sender_domain': ''
            }
        }

    def _clean_text(self, text):
        """Clean and normalize text."""
        return text.lower().strip()

    def _check_urgency(self, text):
        """Check for urgency-related keywords."""
        urgency_words = ['urgent', 'immediate', 'action required', 'verify']
        return any(word in text.lower() for word in urgency_words)

    def _check_links(self, text):
        """Check for suspicious links."""
        import re
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        return len(urls) > 0

    def _extract_sender_domain(self, sender):
        """Extract domain from sender email address."""
        try:
            if '@' in sender:
                domain = sender.split('@')[-1]
                return domain.lower()
            return ''
        except:
            return ''

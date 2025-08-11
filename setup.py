from setuptools import setup, find_packages

setup(
    name="ai-phishing-detection",
    version="1.0.0",
    description="AI-Driven Phishing Detection Using Email Headers and Content Analysis",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "nltk>=3.8.0",
        "beautifulsoup4>=4.12.0",
        "requests>=2.31.0",
        "flask>=2.3.0",
        "transformers>=4.30.0",
        "torch>=2.0.0",
        "xgboost>=1.7.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",  
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)

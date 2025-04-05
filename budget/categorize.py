"""
Transaction categorization module using rule-based and AI-based methods.
"""
import pandas as pd
import numpy as np
import re
import os
from pathlib import Path
import joblib
from datetime import datetime

from .config import DEFAULT_CATEGORIES, AI_MODEL, AI_API
from .logger import logger
from .ai_tools import AITools

class Categorizer:
    """
    Class for categorizing financial transactions using rules and/or ML.
    """
    
    def __init__(self, custom_categories=None):
        """
        Initialize the categorizer with default or custom categories.
        
        Args:
            custom_categories (dict, optional): Custom categories dict with format {category: [keywords]}
        """
        self.categories = custom_categories if custom_categories else DEFAULT_CATEGORIES
        self.ai_model = None
        self.model_loaded = False
        
        # Initialize AI tools for API-based categorization
        self.ai_tools = AITools()
        
        # Try to load pre-trained model if AI is enabled
        if AI_MODEL['enabled']:
            self._load_model()
            
    def _load_model(self):
        """Load a pre-trained categorization model if available."""
        model_path = AI_MODEL['model_path']
        
        if not isinstance(model_path, Path):
            model_path = Path(model_path)
            
        if model_path.exists():
            try:
                self.ai_model = joblib.load(model_path)
                self.model_loaded = True
                logger.info(f"Loaded AI categorization model from {model_path}")
            except Exception as e:
                logger.error(f"Error loading AI model: {str(e)}", exc_info=True)
                self.model_loaded = False
        else:
            logger.info(f"No AI model found at {model_path}")
            self.model_loaded = False
            
    def save_model(self):
        """Save the trained AI model."""
        if not self.ai_model:
            logger.warning("No AI model to save")
            return False
            
        model_path = AI_MODEL['model_path']
        
        if not isinstance(model_path, Path):
            model_path = Path(model_path)
            
        # Ensure directory exists
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            joblib.dump(self.ai_model, model_path)
            logger.info(f"Saved AI model to {model_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving AI model: {str(e)}", exc_info=True)
            return False
            
    def categorize_transaction(self, description, amount=0, date=None):
        """
        Categorize a single transaction using rules or AI.
        
        Args:
            description (str): Transaction description
            amount (float, optional): Transaction amount
            date (datetime, optional): Transaction date
            
        Returns:
            str: Category name
        """
        # Convert date to string format if it's a datetime
        date_str = date.strftime("%Y-%m-%d") if date else datetime.now().strftime("%Y-%m-%d")
        
        # Try using API-based categorization first if enabled
        if self.ai_tools.is_enabled() and AI_API['capabilities']['transaction_categorization']:
            try:
                result = self.ai_tools.categorize_transaction(description, amount, date_str)
                if result and result['confidence'] >= AI_MODEL['confidence_threshold']:
                    logger.debug(f"API categorized '{description}' as '{result['category']}' with confidence {result['confidence']}")
                    return result['category']
            except Exception as e:
                logger.warning(f"API categorization failed: {str(e)}")
        
        # Try using ML model if available
        if self.model_loaded:
            try:
                category = self._categorize_with_model(description)
                return category
            except Exception as e:
                logger.warning(f"ML categorization failed: {str(e)}")
        
        # Fall back to rule-based categorization
        return self._categorize_with_rules(description)
        
    def _categorize_with_model(self, description):
        """
        Categorize a transaction using the ML model.
        
        Args:
            description (str): Transaction description
            
        Returns:
            str: Category name
        """
        if not self.model_loaded or not self.ai_model:
            return self._categorize_with_rules(description)
            
        try:
            # Preprocess description
            processed_desc = description.lower()
            
            # Extract features (depends on how model was trained)
            vectorizer = self.ai_model.get('vectorizer')
            if vectorizer:
                features = vectorizer.transform([processed_desc])
                
                # Make prediction
                classifier = self.ai_model.get('classifier')
                if classifier:
                    prediction = classifier.predict(features)[0]
                    
                    # Convert prediction back to category name
                    encoder = self.ai_model.get('encoder')
                    if encoder:
                        category = encoder.inverse_transform([prediction])[0]
                        return category
            
            # If any step fails, fall back to rules
            return self._categorize_with_rules(description)
            
        except Exception as e:
            logger.warning(f"Error in ML categorization: {str(e)}")
            return self._categorize_with_rules(description)
            
    def _categorize_with_rules(self, description):
        """
        Categorize a transaction using keyword rules.
        
        Args:
            description (str): Transaction description
            
        Returns:
            str: Category name
        """
        description = description.lower()
        
        # Check each category's keywords
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword.lower() in description:
                    return category
        
        # If no match is found
        return 'miscellaneous'
        
    def categorize_transactions(self, transactions_df):
        """
        Categorize multiple transactions in a DataFrame.
        
        Args:
            transactions_df (pd.DataFrame): DataFrame with at least 'description' column
            
        Returns:
            pd.DataFrame: DataFrame with added 'category' column
        """
        if 'description' not in transactions_df.columns:
            logger.error("Transactions DataFrame must have a 'description' column")
            return transactions_df
            
        # Create a copy to avoid modifying the original
        df = transactions_df.copy()
        
        # Get amount and date columns if they exist
        amount_col = None
        date_col = None
        
        if 'amount' in df.columns:
            amount_col = 'amount'
        
        if 'date' in df.columns:
            date_col = 'date'
            
        # Apply categorization to each transaction
        categories = []
        
        for _, row in df.iterrows():
            desc = row['description']
            amount = row[amount_col] if amount_col else 0
            date = row[date_col] if date_col else None
            
            category = self.categorize_transaction(desc, amount, date)
            categories.append(category)
            
        df['category'] = categories
        
        return df
        
    def train_model(self, transactions_df, category_col='category', description_col='description'):
        """
        Train a machine learning model to categorize transactions.
        
        Args:
            transactions_df (pd.DataFrame): DataFrame with transactions
            category_col (str): Column name for categories
            description_col (str): Column name for descriptions
            
        Returns:
            bool: True if training was successful, False otherwise
        """
        from sklearn.feature_extraction.text import CountVectorizer
        from sklearn.preprocessing import LabelEncoder
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.pipeline import Pipeline
        
        if len(transactions_df) < AI_MODEL['min_samples']:
            logger.warning(f"Not enough samples for training (min {AI_MODEL['min_samples']} required)")
            return False
            
        try:
            # Prepare data
            X = transactions_df[description_col].astype(str).str.lower()
            y = transactions_df[category_col]
            
            # Remove rows with missing values
            mask = ~(X.isna() | y.isna())
            X = X[mask]
            y = y[mask]
            
            if len(X) < AI_MODEL['min_samples']:
                logger.warning(f"Not enough valid samples after filtering (min {AI_MODEL['min_samples']} required)")
                return False
                
            # Create feature extraction and encoding components
            vectorizer = CountVectorizer(max_features=500, stop_words='english', ngram_range=(1, 2))
            encoder = LabelEncoder()
            
            # Fit encoder
            y_encoded = encoder.fit_transform(y)
            
            # Create and train classifier
            classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            
            # Fit vectorizer and classifier
            X_features = vectorizer.fit_transform(X)
            classifier.fit(X_features, y_encoded)
            
            # Store model components
            self.ai_model = {
                'vectorizer': vectorizer,
                'encoder': encoder,
                'classifier': classifier
            }
            
            self.model_loaded = True
            
            # Save model
            self.save_model()
            
            logger.info(f"Successfully trained model on {len(X)} transactions with {len(encoder.classes_)} categories")
            return True
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}", exc_info=True)
            return False
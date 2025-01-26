# enhanced_model.py
import numpy as np
import spacy
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer  # Add this import
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

class EnhancedReviewDetector:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 3),
            min_df=2
        )
        self.model = RandomForestClassifier(
            n_estimators=100,
            random_state=42
        )
        try:
            self.nlp = spacy.load('en_core_web_sm')
        except:
            import subprocess
            subprocess.run(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
            self.nlp = spacy.load('en_core_web_sm')

    def extract_linguistic_features(self, text):
        doc = self.nlp(text)
        
        # Basic counts
        num_sentences = len(list(doc.sents))
        avg_word_length = np.mean([len(token.text) for token in doc if not token.is_punct])
        num_exclamations = text.count('!')
        num_questions = text.count('?')
        
        # POS tag ratios
        num_tokens = len(doc)
        adj_ratio = len([token for token in doc if token.pos_ == 'ADJ']) / num_tokens if num_tokens > 0 else 0
        adv_ratio = len([token for token in doc if token.pos_ == 'ADV']) / num_tokens if num_tokens > 0 else 0
        
        # Capitalization and punctuation
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if len(text) > 0 else 0
        punct_ratio = len([token for token in doc if token.is_punct]) / num_tokens if num_tokens > 0 else 0
        
        return np.array([
            num_sentences,
            avg_word_length,
            num_exclamations,
            num_questions,
            adj_ratio,
            adv_ratio,
            caps_ratio,
            punct_ratio
        ])

    def analyze_sentiment(self, doc):
        # Extended sentiment word lists
        positive_words = {
            'excellent', 'amazing', 'wonderful', 'fantastic', 'outstanding',
            'great', 'good', 'best', 'perfect', 'awesome', 'superb'
        }
        negative_words = {
            'terrible', 'horrible', 'awful', 'bad', 'poor', 'worst',
            'disappointing', 'useless', 'waste', 'defective'
        }
        
        words = [token.text.lower() for token in doc]
        positive_count = sum(word in positive_words for word in words)
        negative_count = sum(word in negative_words for word in words)
        
        # Calculate sentiment metrics
        sentiment_score = (positive_count - negative_count) / len(words) if words else 0
        emotion_intensity = (positive_count + negative_count) / len(words) if words else 0
        
        return np.array([sentiment_score, emotion_intensity])

    def fit(self, reviews, labels):
        # Text features
        X_text = self.vectorizer.fit_transform(reviews)
        
        # Additional features
        X_linguistic = np.vstack([
            self.extract_linguistic_features(review) for review in reviews
        ])
        X_sentiment = np.vstack([
            self.analyze_sentiment(self.nlp(review)) for review in reviews
        ])
        
        # Combine all features
        X_combined = np.hstack([
            X_text.toarray(),
            X_linguistic,
            X_sentiment
        ])
        
        # Train the model
        self.model.fit(X_combined, labels)

    def predict(self, review):
        # Process text
        doc = self.nlp(review)
        
        # Extract features
        X_text = self.vectorizer.transform([review]).toarray()
        X_linguistic = self.extract_linguistic_features(review).reshape(1, -1)
        X_sentiment = self.analyze_sentiment(doc).reshape(1, -1)
        
        # Combine features
        X_combined = np.hstack([X_text, X_linguistic, X_sentiment])
        
        # Make prediction
        prediction = self.model.predict(X_combined)[0]
        probability = self.model.predict_proba(X_combined)[0]
        
        # Get feature importance
        feature_importance = self._get_feature_importance(review, doc)
        
        return {
            'prediction': 'Genuine' if prediction == 1 else 'Fake',
            'confidence': float(max(probability)),
            'features': feature_importance
        }
    
    def _get_feature_importance(self, review, doc):
        return {
            'text_stats': {
                'length': len(review),
                'num_sentences': len(list(doc.sents)),
                'avg_word_length': np.mean([len(token.text) for token in doc if not token.is_punct])
            },
            'style_markers': {
                'exclamations': review.count('!'),
                'questions': review.count('?'),
                'capitals_ratio': sum(1 for c in review if c.isupper()) / len(review) if len(review) > 0 else 0
            },
            'linguistic_analysis': {
                'adj_ratio': len([token for token in doc if token.pos_ == 'ADJ']) / len(doc) if len(doc) > 0 else 0,
                'adv_ratio': len([token for token in doc if token.pos_ == 'ADV']) / len(doc) if len(doc) > 0 else 0
            },
            'sentiment': {
                'score': float(self.analyze_sentiment(doc)[0]),
                'intensity': float(self.analyze_sentiment(doc)[1])
            }
        }
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta

class MarketPredictor:
    def __init__(self):
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        
    def prepare_features(self, data):
        """Prepare features for prediction."""
        df = data.copy()
        
        # Technical indicators
        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['volatility'] = df['Close'].rolling(window=10).std()
        df['momentum'] = df['Close'] - df['Close'].shift(5)
        
        # Remove NaN values
        df = df.dropna()
        
        # Feature selection
        features = ['Open', 'High', 'Low', 'Volume', 'SMA_5', 'SMA_20', 'volatility', 'momentum']
        X = df[features]
        y = df['Close']
        
        return X, y
        
    def train(self, historical_data):
        """Train the model on historical data."""
        X, y = self.prepare_features(historical_data)
        
        if len(X) < 30:  # Minimum data requirement
            return False
            
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        return True
        
    def predict_trend(self, historical_data, days_ahead=5):
        """Predict trend for the next few days."""
        X, _ = self.prepare_features(historical_data)
        
        if len(X) < 30:
            return None, None
            
        X_scaled = self.scaler.transform(X)
        last_price = historical_data['Close'].iloc[-1]
        
        # Predict next value
        prediction = self.model.predict(X_scaled[-1:])
        predicted_change = ((prediction[0] - last_price) / last_price) * 100
        
        # Determine trend
        if predicted_change > 1:
            trend = "Strong Bullish"
        elif predicted_change > 0:
            trend = "Bullish"
        elif predicted_change > -1:
            trend = "Bearish"
        else:
            trend = "Strong Bearish"
            
        confidence_score = abs(min(max(predicted_change / 5, 0), 1))
        
        return {
            'trend': trend,
            'predicted_change': predicted_change,
            'confidence': confidence_score,
            'predicted_price': prediction[0],
            'prediction_date': datetime.now() + timedelta(days=days_ahead)
        }

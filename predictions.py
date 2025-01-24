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
        try:
            df = data.copy()

            # Technical indicators
            df['SMA_5'] = df['Close'].rolling(window=5).mean()
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['volatility'] = df['Close'].rolling(window=10).std()
            df['momentum'] = df['Close'] - df['Close'].shift(5)

            # Remove NaN values
            df = df.dropna()

            if len(df) < 30:  # Minimum data requirement
                return None, None

            # Feature selection
            features = ['Open', 'High', 'Low', 'Volume', 'SMA_5', 'SMA_20', 'volatility', 'momentum']
            X = df[features]
            y = df['Close']

            return X, y
        except Exception as e:
            print(f"Error preparing features: {str(e)}")
            return None, None

    def train(self, historical_data):
        """Train the model on historical data."""
        try:
            if historical_data is None or historical_data.empty:
                return False

            X, y = self.prepare_features(historical_data)
            if X is None or y is None:
                return False

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Train model
            self.model.fit(X_scaled, y)
            return True
        except Exception as e:
            print(f"Error training model: {str(e)}")
            return False

    def predict_trend(self, historical_data, days_ahead=5):
        """Predict trend for the next few days."""
        try:
            if historical_data is None or historical_data.empty:
                return None

            X, _ = self.prepare_features(historical_data)
            if X is None:
                return None

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
        except Exception as e:
            print(f"Error predicting trend: {str(e)}")
            return None
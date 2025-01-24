import pandas as pd
from datetime import datetime

class AlertSystem:
    def __init__(self):
        self.alerts = []
        self.alert_thresholds = {
            'price_change': 0.05,  # 5% price change
            'volume_spike': 2.0,   # 2x average volume
            'volatility': 0.15     # 15% volatility
        }

    def set_threshold(self, alert_type, value):
        """Update alert thresholds."""
        if alert_type in self.alert_thresholds:
            self.alert_thresholds[alert_type] = value

    def check_price_alerts(self, portfolio, market_data):
        """Check for price-based alerts."""
        for _, position in portfolio.holdings.iterrows():
            symbol = position['Symbol']
            data = market_data.get_stock_data(symbol, period='5d')
            
            if not data.empty:
                current_price = data['Close'].iloc[-1]
                prev_price = data['Close'].iloc[-2]
                price_change = (current_price - prev_price) / prev_price
                
                if abs(price_change) > self.alert_thresholds['price_change']:
                    self.add_alert(
                        symbol,
                        f"Price changed by {price_change:.2%}",
                        'price'
                    )

    def check_market_alerts(self, market_data):
        """Check for broad market alerts."""
        indicators = market_data.get_market_indicators()
        
        # Check VIX for market volatility
        if 'Volatility Index' in indicators:
            vix = indicators['Volatility Index']
            if vix > 30:  # High volatility threshold
                self.add_alert(
                    'Market',
                    f"High market volatility detected (VIX: {vix:.2f})",
                    'market'
                )

    def add_alert(self, symbol, message, alert_type):
        """Add new alert to the system."""
        self.alerts.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'message': message,
            'type': alert_type
        })

    def get_alerts(self, limit=10):
        """Get recent alerts."""
        return sorted(self.alerts, key=lambda x: x['timestamp'], reverse=True)[:limit]

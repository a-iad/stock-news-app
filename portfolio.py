import pandas as pd
import numpy as np

class Portfolio:
    def __init__(self):
        self.holdings = pd.DataFrame(columns=['Symbol', 'Shares', 'Entry Price'])

    def add_position(self, symbol, shares, entry_price):
        """Add a new position to the portfolio."""
        new_position = pd.DataFrame({
            'Symbol': [symbol],
            'Shares': [shares],
            'Entry Price': [entry_price]
        })
        self.holdings = pd.concat([self.holdings, new_position], ignore_index=True)

    def remove_position(self, symbol):
        """Remove a position from the portfolio."""
        self.holdings = self.holdings[self.holdings['Symbol'] != symbol]

    def get_portfolio_value(self, market_data):
        """Calculate current portfolio value."""
        total_value = 0
        current_values = []
        
        for _, position in self.holdings.iterrows():
            current_price = market_data.get_stock_data(position['Symbol'], period='1d')
            if not current_price.empty:
                price = current_price['Close'].iloc[-1]
                value = price * position['Shares']
                total_value += value
                current_values.append(value)
            else:
                current_values.append(0)
                
        self.holdings['Current Value'] = current_values
        return total_value

    def calculate_portfolio_risk(self):
        """Calculate portfolio risk metrics."""
        if len(self.holdings) < 1:
            return 0
        
        # Simple diversification score based on number of holdings
        diversification_score = min(len(self.holdings) / 10, 1.0)
        
        # Sector concentration risk (simplified)
        sector_risk = 1.0 - diversification_score
        
        return {
            'diversification_score': diversification_score,
            'sector_risk': sector_risk
        }

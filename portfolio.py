import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

class Portfolio:
    def __init__(self):
        self.holdings = pd.DataFrame(columns=['Symbol', 'Shares', 'Entry Price'])
        print("Initializing portfolio...")  # Debug print
        self.load_portfolio()

    def save_portfolio(self):
        """Save portfolio to a JSON file."""
        try:
            if self.holdings is None or self.holdings.empty:
                print("Warning: Attempting to save empty portfolio")
                self.holdings = pd.DataFrame(columns=['Symbol', 'Shares', 'Entry Price'])

            portfolio_data = self.holdings.to_dict('records')
            with open('portfolio.json', 'w') as f:
                json.dump(portfolio_data, f)
            print(f"Portfolio saved successfully with {len(portfolio_data)} positions")
            return True
        except Exception as e:
            print(f"Error saving portfolio: {str(e)}")
            return False

    def load_portfolio(self):
        """Load portfolio from JSON file."""
        try:
            if os.path.exists('portfolio.json'):
                with open('portfolio.json', 'r') as f:
                    portfolio_data = json.load(f)
                if portfolio_data:
                    self.holdings = pd.DataFrame(portfolio_data)
                    print(f"Portfolio loaded with {len(self.holdings)} positions")
                else:
                    print("Empty portfolio data loaded")
                    self.holdings = pd.DataFrame(columns=['Symbol', 'Shares', 'Entry Price'])
            else:
                print("No portfolio file found, starting fresh")
                self.holdings = pd.DataFrame(columns=['Symbol', 'Shares', 'Entry Price'])
            return True
        except Exception as e:
            print(f"Error loading portfolio: {str(e)}")
            self.holdings = pd.DataFrame(columns=['Symbol', 'Shares', 'Entry Price'])
            return False

    def add_position(self, symbol: str, shares: float, entry_price: float) -> bool:
        """Add a new position to the portfolio."""
        try:
            symbol = str(symbol).upper()
            shares = float(shares)
            entry_price = float(entry_price)

            # Check for existing position
            if not self.holdings.empty and symbol in self.holdings['Symbol'].values:
                print(f"Position already exists for {symbol}")
                return False

            new_position = pd.DataFrame({
                'Symbol': [symbol],
                'Shares': [shares],
                'Entry Price': [entry_price]
            })

            self.holdings = pd.concat([self.holdings, new_position], ignore_index=True)
            save_success = self.save_portfolio()
            print(f"Position added for {symbol}: {shares} shares at ${entry_price}")
            return save_success
        except Exception as e:
            print(f"Error adding position: {str(e)}")
            return False

    def remove_position(self, symbol: str) -> bool:
        """Remove a position from the portfolio."""
        try:
            if self.holdings.empty:
                print("Cannot remove from empty portfolio")
                return False

            initial_len = len(self.holdings)
            self.holdings = self.holdings[self.holdings['Symbol'] != symbol]

            if len(self.holdings) == initial_len:
                print(f"No position found for {symbol}")
                return False

            save_success = self.save_portfolio()
            print(f"Position removed for {symbol}")
            return save_success
        except Exception as e:
            print(f"Error removing position: {str(e)}")
            return False

    def get_positions(self):
        """Get list of current positions."""
        try:
            return self.holdings['Symbol'].tolist() if not self.holdings.empty else []
        except Exception as e:
            print(f"Error getting positions: {str(e)}")
            return []

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
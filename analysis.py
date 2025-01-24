import pandas as pd
import numpy as np

class PortfolioAnalysis:
    @staticmethod
    def calculate_impact_score(portfolio, event_type):
        """Calculate the potential impact score of an event on the portfolio."""
        event_weights = {
            'Fed Interest Rate': 0.8,
            'GDP Report': 0.6,
            'Unemployment Rate': 0.5,
            'Geopolitical': 0.7,
            'Supply Chain': 0.6
        }
        
        base_weight = event_weights.get(event_type, 0.5)
        portfolio_size = len(portfolio.holdings)
        
        if portfolio_size == 0:
            return 0
        
        # Calculate weighted impact score
        impact_score = base_weight * (1 + np.log10(portfolio_size))
        return min(impact_score, 1.0)

    @staticmethod
    def analyze_sector_exposure(portfolio):
        """Analyze sector exposure of the portfolio."""
        sector_weights = {}
        total_value = portfolio.holdings['Current Value'].sum()
        
        if total_value == 0:
            return {}
            
        for _, position in portfolio.holdings.iterrows():
            # Simplified sector assignment
            sector = 'Technology'  # In real implementation, would fetch from API
            value = position['Current Value']
            weight = value / total_value
            
            if sector in sector_weights:
                sector_weights[sector] += weight
            else:
                sector_weights[sector] = weight
                
        return sector_weights

    @staticmethod
    def generate_risk_report(portfolio, market_data):
        """Generate a comprehensive risk report."""
        risk_metrics = portfolio.calculate_portfolio_risk()
        market_indicators = market_data.get_market_indicators()
        
        report = {
            'portfolio_metrics': risk_metrics,
            'market_conditions': {
                'volatility': market_indicators.get('Volatility Index', 0),
                'market_trend': 'Bullish' if market_indicators.get('S&P 500', 0) > 0 else 'Bearish'
            },
            'recommendation': 'Hold'  # Simplified recommendation
        }
        
        return report

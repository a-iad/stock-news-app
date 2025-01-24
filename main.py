import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from market_data import MarketData
from portfolio import Portfolio
from alerts import AlertSystem
from analysis import PortfolioAnalysis

# Initialize session state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = Portfolio()
if 'alerts' not in st.session_state:
    st.session_state.alerts = AlertSystem()

# Initialize components
market_data = MarketData()
analysis = PortfolioAnalysis()

# Page configuration
st.set_page_config(page_title="Market Alert System", layout="wide")
st.title("Portfolio Impact Analysis Dashboard")

# Sidebar for portfolio management
with st.sidebar:
    st.header("Portfolio Management")
    
    # Add position form
    with st.form("add_position"):
        symbol = st.text_input("Stock Symbol").upper()
        shares = st.number_input("Number of Shares", min_value=0.0)
        price = st.number_input("Entry Price", min_value=0.0)
        
        if st.form_submit_button("Add Position"):
            st.session_state.portfolio.add_position(symbol, shares, price)
            st.success(f"Added {shares} shares of {symbol}")

# Main dashboard
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Portfolio Overview")
    
    # Portfolio table
    if not st.session_state.portfolio.holdings.empty:
        portfolio_value = st.session_state.portfolio.get_portfolio_value(market_data)
        st.dataframe(st.session_state.portfolio.holdings)
        st.metric("Total Portfolio Value", f"${portfolio_value:,.2f}")
        
        # Portfolio visualization
        fig = px.pie(st.session_state.portfolio.holdings, 
                    values='Current Value', 
                    names='Symbol',
                    title='Portfolio Composition')
        st.plotly_chart(fig)
    else:
        st.info("Add positions to your portfolio to get started")

with col2:
    st.subheader("Market Indicators")
    indicators = market_data.get_market_indicators()
    for name, value in indicators.items():
        st.metric(name, f"{value:,.2f}")

# Alerts section
st.header("Market Alerts")
col3, col4 = st.columns([1, 2])

with col3:
    st.subheader("Recent Alerts")
    # Check for new alerts
    st.session_state.alerts.check_price_alerts(st.session_state.portfolio, market_data)
    st.session_state.alerts.check_market_alerts(market_data)
    
    # Display alerts
    for alert in st.session_state.alerts.get_alerts():
        with st.container():
            st.warning(f"**{alert['symbol']}**: {alert['message']}")

with col4:
    st.subheader("Economic Calendar")
    calendar = market_data.get_economic_calendar()
    st.dataframe(calendar)

# Risk Analysis
st.header("Risk Analysis")
if not st.session_state.portfolio.holdings.empty:
    risk_report = analysis.generate_risk_report(st.session_state.portfolio, market_data)
    
    col5, col6 = st.columns(2)
    
    with col5:
        st.subheader("Portfolio Metrics")
        metrics = risk_report['portfolio_metrics']
        st.metric("Diversification Score", f"{metrics['diversification_score']:.2%}")
        st.metric("Sector Risk", f"{metrics['sector_risk']:.2%}")
    
    with col6:
        st.subheader("Market Conditions")
        conditions = risk_report['market_conditions']
        st.metric("Market Volatility", conditions['volatility'])
        st.metric("Market Trend", conditions['market_trend'])
else:
    st.info("Add positions to view risk analysis")

# Footer
st.markdown("---")
st.caption("Market data is provided for informational purposes only.")

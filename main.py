import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta

from market_data import MarketData
from portfolio import Portfolio
from alerts import AlertSystem

# Page configuration
st.set_page_config(page_title="Market Intelligence Dashboard", layout="wide")

# Initialize components
print("Initializing application components...")
market_data = MarketData()

# Initialize session state
if 'portfolio' not in st.session_state:
    print("Creating new portfolio in session state")
    st.session_state.portfolio = Portfolio()
if 'alerts' not in st.session_state:
    st.session_state.alerts = AlertSystem()
if 'show_add_position' not in st.session_state:
    st.session_state.show_add_position = False

# Navigation bar
with st.container():
    col1, col2, col3 = st.columns([2, 8, 2])
    with col1:
        st.title("Market Intel")
    with col3:
        if st.button("➕ Add Position", type="primary"):
            st.session_state.show_add_position = True

# Modal for adding position
if st.session_state.show_add_position:
    with st.container():
        st.markdown("### Add New Position")
        with st.form("add_position_form"):
            symbol = st.text_input("Stock Symbol").upper()
            shares = st.number_input("Number of Shares", min_value=0.0, step=1.0)
            price = st.number_input("Entry Price", min_value=0.0, step=0.01)

            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("Add Position")
            with col2:
                if st.form_submit_button("Cancel"):
                    st.session_state.show_add_position = False
                    st.rerun()

            if submitted and symbol and shares > 0 and price > 0:
                try:
                    # Verify stock exists
                    stock_data = market_data.get_stock_data(symbol, period='1d')
                    if not stock_data.empty:
                        if st.session_state.portfolio.add_position(symbol, shares, price):
                            st.success(f"Added {shares} shares of {symbol}")
                            st.session_state.show_add_position = False
                            st.rerun()
                        else:
                            st.error("Failed to add position")
                    else:
                        st.error(f"Invalid symbol: {symbol}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# Get current holdings
print("Loading portfolio positions...")
holdings = st.session_state.portfolio.holdings

# Display stocks in tabs
if not holdings.empty:
    print(f"Found {len(holdings)} positions")
    stocks = holdings['Symbol'].tolist()

    # Create tabs for each stock
    if stocks:
        tabs = st.tabs(stocks)

        for tab, symbol in zip(tabs, stocks):
            with tab:
                try:
                    stock_data = market_data.get_stock_data(symbol, period='1mo')
                    if not stock_data.empty:
                        # Price display
                        current_price = stock_data['Close'].iloc[-1]
                        prev_close = stock_data['Close'].iloc[-2]
                        price_change = current_price - prev_close
                        price_change_pct = (price_change / prev_close) * 100

                        st.markdown(f"### ${current_price:.2f} USD")
                        st.markdown(f"{price_change:+.2f} ({price_change_pct:+.2f}%) today")

                        # Price chart
                        fig = px.line(stock_data, x=stock_data.index, y='Close',
                                    title=None)
                        fig.update_layout(
                            showlegend=False,
                            xaxis_title=None,
                            yaxis_title=None,
                            margin=dict(l=0, r=0, t=0, b=0)
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        # Metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Open", f"${stock_data['Open'].iloc[-1]:.2f}")
                            st.metric("High", f"${stock_data['High'].iloc[-1]:.2f}")
                            st.metric("Low", f"${stock_data['Low'].iloc[-1]:.2f}")

                        # Remove position button
                        if st.button("Remove Position", key=f"remove_{symbol}"):
                            if st.session_state.portfolio.remove_position(symbol):
                                st.success(f"Removed {symbol}")
                                st.rerun()
                            else:
                                st.error(f"Failed to remove {symbol}")
                    else:
                        st.error(f"Could not load data for {symbol}")
                except Exception as e:
                    st.error(f"Error displaying {symbol}: {str(e)}")
else:
    st.info("Add positions to your portfolio to view stock analysis")

# Footer
st.markdown("---")
st.caption("Market data is provided for informational purposes only.")
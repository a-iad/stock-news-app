import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta

from market_data import MarketData
from portfolio import Portfolio
from alerts import AlertSystem

# Initialize components
print("Initializing application components...")
market_data = MarketData()

# Page configuration
st.set_page_config(page_title="Market Intelligence Dashboard", layout="wide")

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
        symbol = st.text_input("Stock Symbol").upper()
        shares = st.number_input("Number of Shares", min_value=0.0, step=1.0)
        price = st.number_input("Entry Price", min_value=0.0, step=0.01)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Add Position"):
                if symbol and shares > 0 and price > 0:
                    try:
                        # Verify stock exists
                        stock_data = market_data.get_stock_data(symbol, period='1d')
                        if not stock_data.empty:
                            if st.session_state.portfolio.add_position(symbol, shares, price):
                                st.success(f"Added {shares} shares of {symbol}")
                                st.session_state.show_add_position = False
                                # Clear session state to force refresh
                                st.session_state.portfolio = Portfolio()
                                st.experimental_rerun()
                            else:
                                st.error(f"Failed to add position to portfolio")
                        else:
                            st.error(f"Invalid symbol: {symbol}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.error("Please fill in all fields correctly")
        with col2:
            if st.button("Cancel"):
                st.session_state.show_add_position = False
                st.experimental_rerun()

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
                    print(f"Fetching data for {symbol}...")  # Debug print
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

                        # Additional metrics
                        ticker_info = market_data.get_ticker_info(symbol)
                        if ticker_info:
                            with col2:
                                st.metric("Market Cap", f"{ticker_info.get('marketCap', 'N/A')}")
                                st.metric("P/E Ratio", f"{ticker_info.get('trailingPE', 'N/A'):.2f}")
                            with col3:
                                st.metric("Div Yield", f"{ticker_info.get('dividendYield', 0)*100:.3f}%")

                        # News section
                        st.markdown("## Recent Market News")
                        try:
                            st.info(f"Loading news for {symbol}...")
                            news_data = market_data.get_news_analysis(symbol)

                            if news_data and news_data.get('articles'):
                                for article in news_data['articles']:
                                    with st.container():
                                        st.markdown("---")
                                        st.markdown(f"### {article['title']}")
                                        analysis = article.get('analysis', {})
                                        if analysis and analysis.get('significance'):
                                            st.write(analysis['significance'])
                                            st.info(f"Market Impact: {analysis.get('market_impact', 'Ambivalent')}")
                                            st.caption(f"Published: {article.get('published_at', 'N/A')}")
                            else:
                                st.warning("No recent news available for this stock.")
                        except Exception as e:
                            st.error(f"Error loading news: {str(e)}")

                        # Remove position button
                        if st.button("Remove Position", key=f"remove_{symbol}"):
                            if st.session_state.portfolio.remove_position(symbol):
                                st.success(f"Removed {symbol}")
                                # Clear session state to force refresh
                                st.session_state.portfolio = Portfolio()
                                st.experimental_rerun()
                            else:
                                st.error(f"Failed to remove {symbol}")
                    else:
                        st.error(f"Could not load data for {symbol}")
                except Exception as e:
                    st.error(f"Error displaying {symbol}: {str(e)}")
                    print(f"Error for {symbol}: {str(e)}")  # Debug print
else:
    st.info("Add positions to your portfolio to view stock analysis")

# Footer
st.markdown("---")
st.caption("Market data is provided for informational purposes only.")
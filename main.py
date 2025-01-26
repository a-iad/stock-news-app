import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta

from market_data import MarketData
from portfolio import Portfolio
from alerts import AlertSystem

# Initialize session state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = Portfolio()
if 'alerts' not in st.session_state:
    st.session_state.alerts = AlertSystem()
if 'selected_period' not in st.session_state:
    st.session_state.selected_period = 'day'
if 'show_add_position' not in st.session_state:
    st.session_state.show_add_position = False

# Initialize components
market_data = MarketData()

# Page configuration
st.set_page_config(page_title="Market Intelligence Dashboard", layout="wide")

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
        with st.form("add_position_modal"):
            symbol = st.text_input("Stock Symbol").upper()
            shares = st.number_input("Number of Shares", min_value=0.0)
            price = st.number_input("Entry Price", min_value=0.0)

            col1, col2 = st.columns([1, 1])
            with col1:
                submit = st.form_submit_button("Add Position")
            with col2:
                if st.form_submit_button("Cancel"):
                    st.session_state.show_add_position = False
                    st.rerun()

            if submit and symbol and shares and price:
                st.session_state.portfolio.add_position(symbol, shares, price)
                st.session_state.show_add_position = False
                st.success(f"Added {shares} shares of {symbol}")
                st.rerun()

# Period selector for all stocks
if not st.session_state.portfolio.holdings.empty:
    period_options = {
        'day': '1d',
        'week': '5d',
        'month': '1mo'
    }
    selected_period = st.selectbox(
        "Select Time Period",
        options=list(period_options.keys()),
        format_func=lambda x: x.capitalize(),
        key='period_selector'
    )
    st.session_state.selected_period = selected_period

    # Display stocks and their news vertically
    stocks = st.session_state.portfolio.holdings['Symbol'].tolist()

    for symbol in stocks:
        st.markdown("---")
        st.markdown(f"## {symbol}")

        # Stock data
        stock_data = market_data.get_stock_data(symbol, period=period_options[selected_period])
        if not stock_data.empty:
            current_price = stock_data['Close'].iloc[-1]
            price_change = ((current_price - stock_data['Close'].iloc[0]) / stock_data['Close'].iloc[0]) * 100
            st.metric(
                "Current Price",
                f"${current_price:.2f}",
                f"{price_change:+.2f}% ({selected_period})"
            )

        # Remove button
        if st.button("Remove", key=f"remove_{symbol}"):
            st.session_state.portfolio.remove_position(symbol)
            st.rerun()

        # News section
        st.subheader("Recent Market News")
        news_data = market_data.get_news_analysis(symbol)

        if news_data and news_data.get('articles'):
            for article in news_data['articles']:
                st.markdown("---")

                # Title
                st.markdown(f"### {article['title']}")

                # Analysis
                analysis = article.get('analysis', {})
                if analysis and analysis.get('significance'):
                    st.text("Analysis:")
                    st.write(analysis['significance'])

                # Market Impact
                impact = analysis.get('market_impact', 'Ambivalent')
                st.text(f"Market Impact: {impact}")

                # Date
                st.text(f"Published: {article.get('published_at', 'N/A')}")
                st.markdown(" ")  # Add space between articles
        else:
            st.info("No recent news available for this stock.")

else:
    st.info("Add positions to your portfolio to view stock analysis")

# Footer
st.markdown("---")
st.caption("Market data is provided for informational purposes only.")
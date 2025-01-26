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

        # Stock header with price info
        with st.container():
            col1, col2 = st.columns([6, 2])
            with col1:
                st.markdown(f"## {symbol}")
            with col2:
                if st.button("Remove", key=f"remove_{symbol}"):
                    st.session_state.portfolio.remove_position(symbol)
                    st.rerun()

            stock_data = market_data.get_stock_data(symbol, period=period_options[selected_period])
            if not stock_data.empty:
                current_price = stock_data['Close'].iloc[-1]
                price_change = ((current_price - stock_data['Close'].iloc[0]) / stock_data['Close'].iloc[0]) * 100
                st.metric(
                    "Current Price",
                    f"${current_price:.2f}",
                    f"{price_change:+.2f}% ({selected_period})"
                )

        # News section
        st.subheader("Recent Market News")
        news_data = market_data.get_news_analysis(symbol)

        # Display news articles
        if news_data and news_data.get('articles'):
            for article in news_data['articles']:
                with st.container():
                    st.markdown("---")

                    # Article title
                    st.markdown(f"### {article['title']}")

                    # Summary and Analysis
                    if article.get('article_summary'):
                        st.markdown(f"""
                        <div style='margin-bottom: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px;'>
                            <strong>Summary:</strong><br>
                            {article['article_summary']}
                        </div>
                        """, unsafe_allow_html=True)

                    # Market Impact
                    analysis = article.get('analysis', {})
                    impact = analysis.get('market_impact', 'Ambivalent')

                    impact_colors = {
                        'Very Positive': '#1b5e20',
                        'Somewhat Positive': '#2e7d32',
                        'Ambivalent': '#666666',
                        'Somewhat Negative': '#c62828',
                        'Very Negative': '#b71c1c'
                    }
                    impact_color = impact_colors.get(impact, '#666666')

                    col1, col2 = st.columns([4, 1])

                    with col1:
                        # Enhanced Why It Matters section
                        if analysis.get('significance'):
                            st.markdown(f"""
                            <div style='margin-top: 20px; padding: 20px; background-color: #f0f2f6; border-radius: 5px;'>
                                <h4 style='margin-bottom: 10px; color: #1a237e;'>Why It Matters</h4>
                                <p style='font-size: 16px; line-height: 1.6;'>{analysis['significance']}</p>
                            </div>
                            """, unsafe_allow_html=True)

                    with col2:
                        st.markdown(f"""
                        <div style='padding: 15px; border: 2px solid {impact_color}; border-radius: 5px; margin-top: 20px;'>
                            <p style='color: {impact_color}; font-weight: bold; margin-bottom: 10px;'>Market Impact</p>
                            <p style='font-size: 16px; font-weight: bold;'>{impact}</p>
                            <p style='font-style: italic; font-size: 14px;'>{analysis.get('impact_explanation', '')}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    st.caption(f"Published: {article.get('published_at', 'N/A')}")
        else:
            st.info("No recent news available for this stock.")

else:
    st.info("Add positions to your portfolio to view stock analysis")

# Footer
st.markdown("---")
st.caption("Market data is provided for informational purposes only.")
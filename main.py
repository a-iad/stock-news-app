import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta

from market_data import MarketData
from portfolio import Portfolio
from alerts import AlertSystem
from analysis import PortfolioAnalysis

# Initialize session state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = Portfolio()
if 'alerts' not in st.session_state:
    st.session_state.alerts = AlertSystem()
if 'selected_period' not in st.session_state:
    st.session_state.selected_period = 'day'

# Initialize components
market_data = MarketData()

# Page configuration
st.set_page_config(page_title="Market Intelligence Dashboard", layout="wide")
st.title("Market Intelligence Dashboard")

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

    # Portfolio positions with remove buttons
    st.subheader("Current Positions")
    for idx, position in st.session_state.portfolio.holdings.iterrows():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"{position['Symbol']}: {position['Shares']} shares")
        with col2:
            if st.button("Remove", key=f"remove_{position['Symbol']}"):
                st.session_state.portfolio.remove_position(position['Symbol'])
                st.rerun()

# Main dashboard - Stock Cards
if not st.session_state.portfolio.holdings.empty:
    # Period selector
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

    # Create two columns for stock cards
    stocks = st.session_state.portfolio.holdings['Symbol'].tolist()
    col1, col2 = st.columns(2)

    # Distribute stocks between columns
    for i, symbol in enumerate(stocks):
        current_col = col1 if i % 2 == 0 else col2

        with current_col:
            with st.expander(symbol, expanded=True):
                # Get stock data
                stock_data = market_data.get_stock_data(symbol, period=period_options[selected_period])
                if not stock_data.empty:
                    current_price = stock_data['Close'].iloc[-1]
                    price_change = ((current_price - stock_data['Close'].iloc[0]) / stock_data['Close'].iloc[0]) * 100

                    # Price and movement
                    st.metric(
                        "Current Price",
                        f"${current_price:.2f}",
                        f"{price_change:+.2f}% ({selected_period})"
                    )

                    # News and Sentiment Analysis
                    st.subheader("Recent News")

                    # Get news analysis with DeepSeek insights
                    news = market_data.get_news_analysis(symbol)
                    sentiment = market_data.get_sentiment_analysis(symbol)

                    if news and sentiment:
                        # Display key insights
                        if sentiment.get('key_insights'):
                            st.write("**Key Market Insights:**")
                            for insight in sentiment['key_insights']:
                                impact_color = "red" if insight['score'] < 0 else "green"
                                st.markdown(f"""
                                <div style='padding: 10px; border-left: 3px solid {impact_color}; margin-bottom: 10px;'>
                                    <p><strong>Impact:</strong> {insight['impact']}</p>
                                    <p>{insight['title']}</p>
                                </div>
                                """, unsafe_allow_html=True)

                        # Display detailed news analysis
                        st.write("**Recent Articles:**")
                        for article in news[:4]:  # Display up to 4 articles
                            with st.expander(f"📰 {article['title']}", expanded=False):
                                col_news1, col_news2 = st.columns([2, 1])

                                with col_news1:
                                    st.write("**Summary:**")
                                    st.write(article['description'])

                                    if article.get('relevance_explanation'):
                                        st.write("**Why It's Relevant:**")
                                        st.write(article['relevance_explanation'])

                                with col_news2:
                                    if article['analysis'].get('impact'):
                                        sentiment_color = (
                                            "green" if "positive" in article['analysis']['impact'].lower()
                                            else "red" if "negative" in article['analysis']['impact'].lower()
                                            else "gray"
                                        )
                                        st.markdown(f"""
                                        <div style='padding: 5px; border: 1px solid {sentiment_color}; border-radius: 5px;'>
                                            <p><strong>Sentiment Impact:</strong></p>
                                            <p>{article['analysis']['impact']}</p>
                                            <p>Confidence: {article['analysis']['confidence_score']}%</p>
                                        </div>
                                        """, unsafe_allow_html=True)

                                st.caption(f"Published: {article.get('published_at', 'N/A')}")
                    else:
                        st.info("No recent news available for this stock.")
else:
    st.info("Add positions to your portfolio to view stock analysis")

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

# Footer
st.markdown("---")
st.caption("Market data is provided for informational purposes only.")
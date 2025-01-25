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

# Main dashboard
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Portfolio Overview")
    
    if not st.session_state.portfolio.holdings.empty:
        portfolio_value = st.session_state.portfolio.get_portfolio_value(market_data)
        st.dataframe(st.session_state.portfolio.holdings)
        st.metric("Total Portfolio Value", f"${portfolio_value:,.2f}")

        # Add ML Predictions section
        st.subheader("ML Trend Predictions")
        for _, position in st.session_state.portfolio.holdings.iterrows():
            prediction = market_data.get_stock_prediction(position['Symbol'])
            if prediction:
                with st.expander(f"Prediction for {position['Symbol']}"):
                    col_pred1, col_pred2 = st.columns(2)
                    with col_pred1:
                        st.metric("Predicted Trend", prediction['trend'])
                        st.metric("Confidence Score", f"{prediction['confidence']:.2%}")
                    with col_pred2:
                        st.metric("Predicted Change", f"{prediction['predicted_change']:.2%}")
                        st.metric("Target Price", f"${prediction['predicted_price']:.2f}")
                    st.caption(f"Prediction for {prediction['prediction_date'].strftime('%Y-%m-%d')}")

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

    # Market Sentiment Analysis
    st.subheader("Market Sentiment Analysis")
    market_sentiment = market_data.get_market_sentiment()

    if market_sentiment:
        sentiment_score = market_sentiment['market_sentiment']

        # Create a color scale based on sentiment
        if sentiment_score > 0.2:
            sentiment_color = "green"
        elif sentiment_score > 0:
            sentiment_color = "lightgreen"
        elif sentiment_score < -0.2:
            sentiment_color = "red"
        elif sentiment_score < 0:
            sentiment_color = "pink"
        else:
            sentiment_color = "gray"

        st.markdown(f"""
        <div style='padding: 10px; background-color: {sentiment_color}; border-radius: 5px;'>
            <h4>Overall Market Sentiment</h4>
            <p>Score: {sentiment_score:.2f}</p>
            <p>Based on {market_sentiment['analyzed_symbols']} major market symbols</p>
        </div>
        """, unsafe_allow_html=True)

    # Economic News Impact
    st.subheader("Economic News Impact")
    economic_news = market_data.get_economic_news()

    if economic_news:
        st.write(f"Analyzing {economic_news['total_articles']} recent news items")
        for news_item in economic_news['news_items']:
            with st.expander(f"📰 {news_item['title'][:100]}..."):
                st.write(news_item['description'])
                analysis = news_item['analysis']

                # Create columns for analysis details
                col_news1, col_news2 = st.columns(2)
                with col_news1:
                    st.metric("Impact", analysis['impact'])
                    st.metric("Confidence", f"{analysis['confidence_score']}%")
                with col_news2:
                    st.write("Analysis:", analysis['explanation'])

                st.caption(f"Published: {news_item['published_at']}")
                st.markdown(f"[Read more]({news_item['url']})")

    # Individual Stock News
    if not st.session_state.portfolio.holdings.empty:
        st.subheader("Stock-Specific News")
        for _, position in st.session_state.portfolio.holdings.iterrows():
            symbol = position['Symbol']
            news = market_data.get_news_analysis(symbol)

            if news:
                with st.expander(f"📊 Latest News for {symbol}"):
                    for news_item in news[:3]:  # Show top 3 news items
                        st.markdown(f"**{news_item['title']}**")
                        st.write(news_item['description'])

                        # Show analysis results
                        col_stock1, col_stock2 = st.columns(2)
                        with col_stock1:
                            st.metric("Market Impact", news_item['analysis']['impact'])
                        with col_stock2:
                            st.write("Analysis:", news_item['analysis']['explanation'])

                        st.caption(f"Confidence: {news_item['analysis']['confidence_score']}%")
                        st.markdown(f"[Read full article]({news_item['url']})")
                        st.markdown("---")

    # Individual Stock Sentiment
    if not st.session_state.portfolio.holdings.empty:
        st.subheader("Portfolio Sentiment Analysis")
        for _, position in st.session_state.portfolio.holdings.iterrows():
            symbol = position['Symbol']
            sentiment = market_data.get_sentiment_analysis(symbol)

            if sentiment:
                with st.expander(f"Sentiment Analysis for {symbol}"):
                    col_sent1, col_sent2 = st.columns(2)
                    with col_sent1:
                        st.metric("Market Sentiment", sentiment['sentiment_direction'])
                        st.metric("Confidence", f"{sentiment['confidence']:.1f}%")
                    with col_sent2:
                        st.metric("Market Impact", sentiment['market_impact'])
                        st.metric("Analyzed News", sentiment['news_count'])

                    if sentiment['key_insights']:
                        st.subheader("Key Market Insights")
                        for insight in sentiment['key_insights']:
                            impact_color = "red" if insight['score'] < 0 else "green"
                            st.markdown(f"""
                            <div style='padding: 10px; border-left: 3px solid {impact_color};'>
                                <p><strong>Impact Level:</strong> {insight['impact']}</p>
                                <p>{insight['title']}</p>
                            </div>
                            """, unsafe_allow_html=True)

                    st.caption(f"Last updated: {sentiment['timestamp'].strftime('%Y-%m-%d %H:%M')}")


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
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
            shares = st.number_input("Number of Shares", min_value=0.0, step=1.0)
            price = st.number_input("Entry Price", min_value=0.0, step=0.01)

            col1, col2 = st.columns([1, 1])
            with col1:
                submit = st.form_submit_button("Add Position")
            with col2:
                if st.form_submit_button("Cancel"):
                    st.session_state.show_add_position = False
                    st.rerun()

            if submit and symbol and shares > 0 and price > 0:
                try:
                    # Verify the symbol exists
                    stock_data = market_data.get_stock_data(symbol, period='1d')
                    if not stock_data.empty:
                        st.session_state.portfolio.add_position(symbol, shares, price)
                        st.session_state.portfolio.save_portfolio()  # Ensure portfolio is saved
                        st.session_state.show_add_position = False
                        st.success(f"Added {shares} shares of {symbol}")
                        st.rerun()
                    else:
                        st.error(f"Invalid stock symbol: {symbol}")
                except Exception as e:
                    st.error(f"Error adding position: {str(e)}")

# Display stocks in tabs
if not st.session_state.portfolio.holdings.empty:
    stocks = st.session_state.portfolio.holdings['Symbol'].tolist()

    # Create tabs for each stock
    tabs = st.tabs(stocks)

    for tab, symbol in zip(tabs, stocks):
        with tab:
            # Stock data
            stock_data = market_data.get_stock_data(symbol, period='1mo')
            if not stock_data.empty:
                # Current price and change
                current_price = stock_data['Close'].iloc[-1]
                prev_close = stock_data['Close'].iloc[-2]
                price_change = current_price - prev_close
                price_change_pct = (price_change / prev_close) * 100

                # Price display
                st.markdown(f"### ${current_price:.2f} USD")
                st.markdown(f"{price_change:+.2f} ({price_change_pct:+.2f}%) today")

                # After hours (using last available price)
                after_hours = stock_data['Close'].iloc[-1]
                after_hours_change = after_hours - current_price
                after_hours_pct = (after_hours_change / current_price) * 100
                st.caption(f"After hours {after_hours:.2f} {after_hours_change:+.2f} ({after_hours_pct:+.2f}%)")

                # Time scale buttons
                time_scales = ['1D', '5D', '1M', '6M', 'YTD', '1Y', '5Y', 'Max']
                cols = st.columns(len(time_scales))
                selected_scale = None

                for i, scale in enumerate(time_scales):
                    with cols[i]:
                        if st.button(scale, key=f"{symbol}_{scale}"):
                            selected_scale = scale

                # Map button selection to yfinance period
                period_map = {
                    '1D': '1d', '5D': '5d', '1M': '1mo',
                    '6M': '6mo', 'YTD': 'ytd', '1Y': '1y',
                    '5Y': '5y', 'Max': 'max'
                }

                # Default to 1M if no selection
                period = period_map[selected_scale] if selected_scale else '1mo'

                # Fetch data for selected period
                display_data = market_data.get_stock_data(symbol, period=period)

                # Price chart
                fig = px.line(display_data, x=display_data.index, y='Close',
                             title=None)
                fig.update_layout(
                    showlegend=False,
                    xaxis_title=None,
                    yaxis_title=None,
                    margin=dict(l=0, r=0, t=0, b=0)
                )
                st.plotly_chart(fig, use_container_width=True)

                # Key metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Open", f"${stock_data['Open'].iloc[-1]:.2f}")
                    st.metric("High", f"${stock_data['High'].iloc[-1]:.2f}")
                    st.metric("Low", f"${stock_data['Low'].iloc[-1]:.2f}")

                # Get additional stock info
                ticker_info = market_data.get_ticker_info(symbol)
                if ticker_info:
                    with col2:
                        st.metric("Market Cap", f"{ticker_info.get('marketCap', 'N/A')}")
                        st.metric("P/E Ratio", f"{ticker_info.get('trailingPE', 'N/A'):.2f}")
                    with col3:
                        st.metric("Div Yield", f"{ticker_info.get('dividendYield', 0)*100:.3f}%")

            # Remove button
            if st.button("Remove", key=f"remove_{symbol}"):
                st.session_state.portfolio.remove_position(symbol)
                st.rerun()

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

else:
    st.info("Add positions to your portfolio to view stock analysis")

# Footer
st.markdown("---")
st.caption("Market data is provided for informational purposes only.")
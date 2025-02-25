import datetime
import yfinance as yf
import time
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objs as go
from flask import Flask, render_template, request

# Initialize Flask
server = Flask(__name__)

# Initialize Dash with Flask as server
app = Dash(__name__, server=server, routes_pathname_prefix="/dashboard/")


# 🔹 Fetch Stock Price Data
def fetch_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo", interval="1h")
        return hist
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return pd.DataFrame()


# 🔹 Fetch Stock News
def get_news(query, count=5):
    try:
        search_result = yf.Search(query, news_count=count)
        if not search_result or not search_result.news:
            return []

        news_list = []
        for article in search_result.news:
            news_list.append({
                "title": article.get("title", "No Title"),
                "link": article.get("link", "#"),
                "image": article.get("thumbnail", {}).get("resolutions", [{}])[0].get("url",
                                                                                      "https://via.placeholder.com/150")
            })
        return news_list
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []


# 🔹 Create Price Chart
def create_price_chart(df, ticker):
    fig = go.Figure()
    color = "green" if df['Close'].iloc[-1] > df['Close'].iloc[0] else "red"  # Green if stock is up, Red if down
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Close Price', line=dict(color=color)))
    fig.update_layout(title=f"Stock Price: {ticker}")
    return fig


# 🔹 Dash Layout (Stock Chart + Search Bar)
app.layout = html.Div([
    html.H1("BearWatch - Stock News & Charts"),
    dcc.Input(id="search", type="text", placeholder="Enter stock ticker (e.g., AAPL)", debounce=True),
    dcc.Graph(id='price-chart'),  # Stock price chart
])


# 🔹 Dash Callback (Updates Chart)
@app.callback(
    Output('price-chart', 'figure'),
    [Input("search", "value")]
)
def update_price_chart(ticker):
    if not ticker:
        return go.Figure()
    df = fetch_data(ticker)
    if df.empty:
        return go.Figure()
    return create_price_chart(df, ticker)


# 🔹 Flask Route (News Page)
@server.route("/", methods=["GET", "POST"])
def home():
    news_articles = []
    query = "Google"  # Default

    if request.method == "POST":
        query = request.form.get("query")

    news_articles = get_news(query, count=5)
    return render_template("index.html", news=news_articles)


# Run Flask + Dash
if __name__ == "__main__":
    server.run(debug=True)

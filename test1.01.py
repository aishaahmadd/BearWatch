import datetime
import yfinance as yf
import time
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State
import plotly.graph_objs as go
from flask import Flask, render_template, request

# Initialize Flask
server = Flask(__name__)

# Initialize Dash with Flask as server
app = Dash(__name__, server=server, routes_pathname_prefix="/dashboard/")


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



# 🔹 Dash Layout (Stock Chart + Search Bar)
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Graph(id="live-stock-graph"),
    # Interval component to update the graph every 1 second
    dcc.Interval(id="interval-component", interval=1000, n_intervals=0)
])


# 🔹 Dash Callback (Updates Chart)
@app.callback(
    Output("live-stock-graph", "figure"),
    [Input("interval-component", "n_intervals"),
    Input("url", "search")]
)
def update_graph(n, search):
    # Default stock symbol
    stock_symbol = "^GSPC"

    # Extract stock symbol from URL (?stock=AAPL)
    if search:
        query_params = search.lstrip("?").split("&")
        params_dict = dict(param.split("=") for param in query_params if "=" in param)
        stock_symbol = params_dict.get("stock", "^GSPC")

    stock = yf.Ticker(stock_symbol)
    data = stock.history(period="1d", interval="1m")  # Fetch recent minute data

    if not data.empty:
        figure = go.Figure(data=[go.Scatter(
            x=data.index,
            y=data["Close"],
            mode="lines+markers",
            name=stock_symbol
        )])
        figure.update_layout(title=f"Real-Time {stock_symbol} Stock Price",
                             xaxis_title="Time",
                             yaxis_title="Price",
                             xaxis=dict(showgrid=True),
                             yaxis=dict(showgrid=True))
        return figure


# 🔹 Flask Route (News Page)
@server.route("/", methods=["GET", "POST"])
def home():
    stock_symbol = request.args.get("stock", "^GSPC")
    news_articles = []
    query = "Google"  # Default

    if request.method == "POST":
        query = request.form.get("query")

    news_articles = get_news(query, count=5)
    return render_template("home.html", news=news_articles, stock_symbol=stock_symbol)
@server.route('/news.html', methods=["GET", "POST"])
def news():
    news_articles = []
    query = "Google"  # Default

    if request.method == "POST":
        query = request.form.get("query")

    news_articles = get_news(query, count=5)
    return render_template("news.html", news=news_articles)

# Run Flask + Dash
if __name__ == "__main__":
    server.run(debug=True)
    
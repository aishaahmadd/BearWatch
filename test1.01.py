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
   html.H1(children="BearWatch",style={'textAlign':'center'}),  # Title of the dashboard
   # Input for stock symbol
   html.Div([
        dcc.Input(id="stock-input", type="text", value="AAPL", placeholder="Enter stock symbol",
                  style={'marginRight': '10px', 'padding': '10px', 'fontSize': '16px'}),
        html.Button("Submit", id="submit-button", n_clicks=0, style={'padding': '10px', 'fontSize': '16px'})
   ], style={'marginBottom': '20px'}),

   dcc.Graph(id="live-stock-graph"),

    # Interval component to update the graph every 5 seconds
   dcc.Interval(id="interval-component", interval=5000, n_intervals=0)
])


# 🔹 Dash Callback (Updates Chart)
@app.callback(
    Output("live-stock-graph", "figure"),
    [Input("interval-component", "n_intervals"), Input("submit-button", "n_clicks")],
    [State("stock-input", "value")]
)
def update_graph(n, n_clicks, stock_symbol):
    if not stock_symbol:
        stock_symbol = "AAPL"  # Default to AAPL if no input
    
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
    news_articles = []
    query = "Google"  # Default

    if request.method == "POST":
        query = request.form.get("query")

    news_articles = get_news(query, count=5)
    return render_template("index.html", news=news_articles)


# Run Flask + Dash
if __name__ == "__main__":
    server.run(debug=True)

import datetime
import yfinance as yf
import time
import pandas as pd
from dash import dash, dcc, html, Input, Output, callback
import plotly.graph_objs as go
from dash.dependencies import Input, Output
from flask import Flask, render_template, request

server = Flask(__name__)

# Route code from this file to home.html
@server.route("/")
def home():
    stock_symbol = request.args.get("stock", "AAPL")  # Default stock
    return render_template("home.html", stock_symbol=stock_symbol)

# Initialize the Dash app
app = dash.Dash(__name__, server=server, routes_pathname_prefix="/dashboard/")

# Defines the layout of the dashboard
app.layout = html.Div([
   html.H1("BearWatch"),  # Title of the dashboard
   dcc.Input(
      id="search",
      type="text",
      placeholder="Search".format("text"),
      debounce=True
   ),
   dcc.Graph(id='price-chart')  # Placeholder for the price chart
])

# TODO: fetch data from different timeframes
# Fetch historical market data
def fetch_data(ticker):
   stock = yf.Ticker(ticker)
   hist = stock.history(period="1mo",interval="1h")  # Retrieve data for the past year
   return hist


# TODO: Make this update!
# TODO: Make line green if stock is up and red if down
def create_price_chart(df,ticker):
   fig = go.Figure()
   fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Close Price'))
   fig.update_layout(title=str(ticker))
   return fig

# Callback allows user interaction
@app.callback(
   Output('price-chart', 'figure'),
   [Input("search", "value")]
)

# callback function, takes the input from callback and its output goes back to callback
def update_price_chart(ticker):
   df = pd.DataFrame(fetch_data(ticker))
   fig = create_price_chart(df,ticker)
   return fig

# Run the app
if __name__ == '__main__':
   server.run(debug=True)


import datetime
import yfinance as yf
import time
import matplotlib.pyplot as plt
import pandas as pd
from dash import dash, dcc, html, Input, Output, callback
import plotly.graph_objs as go
from dash.dependencies import Input, Output

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the dashboard
app.layout = html.Div([
   html.H1("Custom Trading Dashboard"),  # Title of the dashboard
   dcc.Input(
       id="search",
            type="text",
            placeholder="Search".format("text"),
            debounce=True
   ),
   dcc.Graph(id='price-chart')  # Placeholder for the price chart
])

# Fetch historical market data
def fetch_data(ticker):
   stock = yf.Ticker(ticker)
   hist = stock.history(period="1mo",interval="1h")  # Retrieve data for the past year
   return hist

def create_price_chart(df):
   fig = go.Figure()
   fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Close Price'))
   fig.update_layout(title='Stock Price Over Time', xaxis_title='Date', yaxis_title='Price')
   return fig

@app.callback(
   Output('price-chart', 'figure'),
   [Input("search", "value")]
)
def update_price_chart(ticker):
   df = pd.DataFrame(fetch_data(ticker))
   fig = create_price_chart(df)
   return fig

# Run the app
if __name__ == '__main__':
   app.run_server(debug=True)



'''
Importing stock data (Open, High, Low, Close) for userticker every 10 seconds.
Datetime from output yyyy-mm-dd hh:mm:00 DOES NOT SUPPORT SECONDS.
'''
'''
def fetch_day_data(userticker: str) -> None:
    ticker = yf.Ticker(userticker)
    data = ticker.history(period="1d", interval="1m")
    #print(data.tail(1))  # Display the most recent data point
    print(data)

def display_day_stock_data(ticker: str) -> None:
    while True:
        data = fetch_day_data(ticker)
        time.sleep(10)  # Wait for 10 sec before fetching the data again
'''

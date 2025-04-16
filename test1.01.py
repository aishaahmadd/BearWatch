import yfinance as yf
import dash
from flask import Flask, render_template, request, jsonify
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objs as go
from urllib.parse import parse_qs
from reccomendationsys_update1 import get_company_info, build_feature_matrix, recommend_stocks, get_tickers_from_finviz

# Initialize Flask
server = Flask(__name__)

home_tickers = {
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "Dow Jones": "^DJI"
}

def fetch_stock_data(ticker, pd="1d"):
    intervalsForPeriod = {"1d":"1m", "5d":"1h", "1mo":"1h", "3mo":"1d", "ytd":"1d", "1y":"1d", "max":"1d"}
    stock = yf.Ticker(ticker)
    df = stock.history(period=pd, interval=intervalsForPeriod[pd])
    return df

def determine_color(stock_symbol):
    stock = yf.Ticker(stock_symbol)
    data = fetch_stock_data(stock_symbol)
    current_price = stock.info.get("currentPrice", data["Close"].iloc[-1])
    prev_close = stock.info.get("previousClose", data["Close"].iloc[0])

    # Calculate price change and percentage
    price_change = current_price - prev_close
    percent_change = (price_change / prev_close) * 100

    # Determine line color
    line_color = "green" if price_change > 0 else "red"
    sign = "+" if price_change > 0 else ""
    title = f"""
    {stock.info.get('shortName', stock_symbol)} <br>
    ${current_price:.2f} <span style='color:{line_color};'> <br>
    {sign}${price_change:.2f} ({sign}{percent_change:.2f}%) Today</span>
    """
    return line_color, title


def create_graph(stock_symbol):
    data = fetch_stock_data(stock_symbol)
    line_color, title = determine_color(stock_symbol)

    figure = go.Figure(data=[go.Scatter(
        x=data.index,
        y=data["Close"],
        mode="lines",
        line=dict(color=line_color, width=2),
        name=stock_symbol
    )])

    figure.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title=title,
        title_x=0.5,
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True)
    )

    return figure

#  Dash Home Tabs
appHome=Dash(__name__, server=server, routes_pathname_prefix="/home/")
appHome.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Tabs(id="tabs", value="S&P 500", children=[
        dcc.Tab(label=name, value=name) for name in home_tickers.keys()
    ]),
    html.Div(id="tabs-content")
])

@appHome.callback(
   Output("tabs-content", "children"),
    Input("tabs", "value"),
    Input("url", "search")
    
)
def update_graph(selected_tab, search):
    # Default time range
    time_range = "1d"

    # Parse ?time=1mo
    if search:
        query = parse_qs(search.lstrip("?"))
        time_range = query.get("time", ["1d"])[0]
    
    df = fetch_stock_data(home_tickers[selected_tab], time_range)
    line_color, title = determine_color(home_tickers[selected_tab])
    fig = go.Figure()
    fig.add_trace(
        go.Scatter
            (x=df.index, 
             y=df["Close"], 
             mode="lines",
             line=dict(color=line_color, width=2), 
             name=selected_tab))
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title=title, 
        xaxis_title="Date", 
        yaxis_title="Closing Price")
    return dcc.Graph(figure=fig)


#############################################################################
# Stock Page Graph
#############################################################################
app = Dash(__name__, server=server, routes_pathname_prefix="/dashboard/")

#  News Fetching Functions
# 🔹 Fetch Stock News (With Pagination)
def get_news(query="Stock Market", count=8, offset=0):
    try:
        search_result = yf.Search(query, news_count=(count + offset))
        if not search_result or not search_result.news:
            return []

        news_list = []
        for article in search_result.news[offset:offset + count]:
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
    
def get_stock_news(stock_symbol, count=5):
    try:
        search_result = yf.Search(stock_symbol, news_count=count)
        if not search_result or not search_result.news:
            return []
        return [{
            "title": article.get("title", "No Title"),
            "link": article.get("link", "#")
        } for article in search_result.news[:count]]
    except Exception as e:
        print(f"Stock News Error: {e}")
        return []


def get_latest_financial_news(count=5):
    try:
        search_result = yf.Search("Financial Market", news_count=count)
        if not search_result or not search_result.news:
            return []
        return [{
            "title": article.get("title", "No Title"),
            "link": article.get("link", "#")
        } for article in search_result.news[:count]]
    except Exception as e:
        print(f"Ticker News Error: {e}")
        return []

    
# 🔹 Fetch Similar Stocks//gotten from owens code
def get_similar_stocks(stock_symbol):
    try:
        input_info = get_company_info(stock_symbol)
        sector = input_info['Sector']
        market_cap = input_info['Market Cap']

        if sector != 'N/A':
            tickers = get_tickers_from_finviz(sector, market_cap)
            if tickers:
                df = build_feature_matrix(tickers)
                return recommend_stocks(stock_symbol, df)
    except Exception as e:
        print(f"Error fetching similar stocks: {e}")
    return []

# json {
#     "name" : "Raham",
#     "Array": "1,2,3.4.3"
# }
#test routes using postman separately
#typescript should be calling python routes and should be calling some jyson script we can decode or err codes that we can manipulate the js code

# 🔹 Dash Layout (Stock Chart)
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Graph(id="live-stock-graph"),
    dcc.Interval(id="interval-component", interval=1000, n_intervals=0),  # Auto-update every 1 second
    html.Div(id="recommended-stocks-container", children=[
    html.H3("Recommended Stocks"),
    html.Ul(id="recommended-stocks-list")  # List will be updated dynamically
    ], style={"position": "absolute", "bottom": "20px", "left": "20px", "background-color": "#f1f1f1", "padding": "10px", "display": "none"})
])


# 🔹 Dash Callback (Update Stock Graph)
@app.callback(
    Output("live-stock-graph", "figure"),
    [Input("interval-component", "n_intervals"),
     Input("url", "search")]
)
def update_graph(n, search): #added from owen
    stock_symbol = "^GSPC"

    if search:
        query_params = search.lstrip("?").split("&")
        params_dict = dict(param.split("=") for param in query_params if "=" in param)
        stock_symbol = params_dict.get("stock", "^GSPC")

    data = fetch_stock_data(stock_symbol)
    stock_info = stock.info

    if data.empty or "currentPrice" not in stock_info:
        return go.Figure()

    current_price = stock_info.get("currentPrice", data["Close"].iloc[-1])
    prev_close = stock_info.get("previousClose", data["Close"].iloc[0])

    # Calculate price change and percentage
    price_change = current_price - prev_close
    percent_change = (price_change / prev_close) * 100

    # Determine line color
    line_color = "green" if price_change > 0 else "red"
    sign = "+" if price_change > 0 else ""

    title = f"""
    {stock_info.get('shortName', stock_symbol)} <br>
    ${current_price:.2f} <span style='color:{line_color};'> <br>
    {sign}${price_change:.2f} ({sign}{percent_change:.2f}%) Today</span>
    """

    figure = go.Figure(data=[go.Scatter(
        x=data.index,
        y=data["Close"],
        mode="lines",
        line=dict(color=line_color, width=2),
        name=stock_symbol
    )])

    figure.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title=title,
        title_x=0.5,
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True)
    )

    return figure

# 🔹 Dash Callback (Get Similar Stocks on Stock Change)
@app.callback(
    Output("recommended-stocks-list", "children"),
    Output("recommended-stocks-container", "style"),
    Input("url", "search")
)
def update_stock_recommendation(search):
    if search:
        query_params = search.lstrip("?").split("&")
        params_dict = dict(param.split("=") for param in query_params if "=" in param)
        stock_symbol = params_dict.get("stock", "^GSPC")
        if stock_symbol != "^GSPC":
            similar_stocks = get_similar_stocks(stock_symbol)
            if similar_stocks:
                return [html.Li(stock) for stock in similar_stocks], {"position": "absolute", "bottom": "20px", "left": "20px", "background-color": "#f1f1f1", "padding": "10px", "display": "block"}
    
    return [], {"display": "none"}  # Hide if no valid stock is entered #added from owen


# 🔹 Home Route
@server.route("/", methods=["GET"])
def home():
    #stock_symbol = request.args.get("stock", "^GSPC")
    return render_template("home.html")


# 🔹 News Page Route
@server.route('/news.html', methods=["GET", "POST"])
def news():
    query = "Stock Market"
    if request.method == "POST":
        query = request.form.get("query")

    news_articles = get_news(query, count=8)
    return render_template("news.html", news=news_articles)

@server.route('/load_more_news', methods=["GET"])
def load_more_news():
    query = request.args.get("query", "Stock Market")
    offset = int(request.args.get("offset", 0))
    more_news = get_news(query, count=8, offset=offset)
    return jsonify(more_news)

# 🔹 Stock Page Route
@server.route('/stock', methods=["GET", "POST"])
def stock():
    stock_symbol = request.args.get("stock", "^GSPC").upper()
    stock_news = get_stock_news(stock_symbol, count=5)
    ticker_news = get_latest_financial_news()
    return render_template("stock.html", stock_symbol=stock_symbol, stock_news=stock_news, ticker_news=ticker_news) 


# Run Flask + Dash
if __name__ == "__main__":
    server.run(debug=True)

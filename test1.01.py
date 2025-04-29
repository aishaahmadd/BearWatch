import yfinance as yf
import dash
import requests
from flask import Flask, render_template, request, jsonify
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objs as go
from urllib.parse import parse_qs
from RelatedStocks import get_related_stocks
from StockOverview import get_stock_overview
from AboutStock import get_stock_about
from TrendingStocks import get_trending_stocks

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

def determine_color(stock_symbol, colorblind_mode = False):
    stock = yf.Ticker(stock_symbol)
    data = fetch_stock_data(stock_symbol)
    current_price = stock.info.get("currentPrice", data["Close"].iloc[-1])
    prev_close = stock.info.get("previousClose", data["Close"].iloc[0])

    # Calculate price change and percentage
    price_change = current_price - prev_close
    percent_change = (price_change / prev_close) * 100

    # Determine line color
    if colorblind_mode:
        line_color = "blue" if price_change > 0 else "orange"  
    else:
        line_color = "green" if price_change > 0 else "red"
    sign = "+" if price_change > 0 else ""
    title = f"""
    {stock.info.get('shortName', stock_symbol)} <br>
    ${current_price:.2f} <span style='color:{line_color};'> <br>
    {sign}${price_change:.2f} ({sign}{percent_change:.2f}%) Today</span>
    """
    return line_color, title


def create_graph(stock_symbol, colorblind_mode):
    data = fetch_stock_data(stock_symbol)
    line_color, title = determine_color(stock_symbol, colorblind_mode)

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
    html.Div(id="tabs-container"),
    html.Div(id="tabs-content")
])


@appHome.callback(
    Output("tabs-container", "children"),
    Input("url", "search")
)
def update_tabs(search):
    dark_mode = False
    if search:
        query = parse_qs(search.lstrip("?"))
        dark_mode = query.get("darkmode", ["false"])[0] == "true"

    if dark_mode:
        tab_bg = "#222325"
        tab_text = "#dee4fc"
        tab_selected_bg = "#dee4fc"
        tab_selected_text = "#141417"
        border_color = "#191a1b"
    else:
        tab_bg = "#f0ede7"
        tab_text = "#311f6b"
        tab_selected_bg = "#311f6b"
        tab_selected_text = "#f0ede7"
        border_color = "#f0ede9"

    return dcc.Tabs(
        id="tabs",
        value="S&P 500",
        children=[
            dcc.Tab(label=name, value=name, style={
                "backgroundColor": tab_bg,
                "color": tab_text,
                "border": f"1px solid {border_color}",
                "fontFamily": "Cambria, Georgia, serif",
                "padding": "10px",
                "textAlign": "center",
                "justifyContent": "center",
                "alignItems": "center",
                "display": "flex"
            }, selected_style={
                "backgroundColor": tab_selected_bg,
                "color": tab_selected_text,
                "border": f"1px solid {border_color}",
                "fontFamily": "Cambria, Georgia, serif",
                "padding": "10px",
                "textAlign": "center",
                "justifyContent": "center",
                "alignItems": "center",
                "display": "flex"
            }) for name in home_tickers.keys()
        ],
        style={
            "backgroundColor": tab_bg,
            "borderBottom": f"2px solid {border_color}",
            "fontFamily": "Cambria, Georgia, serif"
        }
    )



@appHome.callback(
    Output("tabs-content", "children"),
    Input("tabs", "value"),
    Input("url", "search")
)
def update_graph(selected_tab, search):
    colorblind_mode = False
    dark_mode = False
    time_range = "1d"

    if search:
        query = parse_qs(search.lstrip("?"))
        time_range = query.get("time", ["1d"])[0]
        colorblind_mode = query.get("colorblind", ["false"])[0] == "true"
        dark_mode = query.get("darkmode", ["false"])[0] == "true"

    df = fetch_stock_data(home_tickers[selected_tab], time_range)
    line_color, title = determine_color(home_tickers[selected_tab], colorblind_mode)

    if dark_mode:
        background_color = "#141417"
        text_color = "#dee4fc"
    else:
        background_color = "#F9F5ED"
        text_color = "#311f6b"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["Close"],
        mode="lines",
        line=dict(color=line_color, width=2),
        name=selected_tab
    ))

    fig.update_layout(
        plot_bgcolor=background_color,
        paper_bgcolor=background_color,
        font=dict(color=text_color),
        title=title,
        title_x=0.5,
        xaxis_title="Time",
        yaxis_title="Closing Price",
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True)
    )

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
            "link": article.get("link", "#"),
            "image": article.get("thumbnail", {}).get("resolutions", [{}])[0].get("url", "https://via.placeholder.com/70")
        } for article in search_result.news[:count]]
    except Exception as e:
        print(f"Stock News Error: {e}")
        return []
    
def get_main_news(query="Stock Market", count=4):
    try:
        search_result = yf.Search(query, news_count=count)
        if not search_result or not search_result.news:
            return []
        return [{
            "title": article.get("title", "No Title"),
            "link": article.get("link", "#"),
            "image": article.get("thumbnail", {}).get("resolutions", [{}])[0].get("url", "https://via.placeholder.com/70")
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
    time_range = "1d"
    colorblind_mode = False
    dark_mode = False

    if search:
        query = parse_qs(search.lstrip("?"))
        stock_symbol = query.get("stock", ["^GSPC"])[0]
        time_range = query.get("time", ["1d"])[0]
        colorblind_mode = query.get("colorblind", ["false"])[0] == "true"
        dark_mode = query.get("darkmode",   ["false"])[0] == "true"

    data = fetch_stock_data(stock_symbol, time_range)
    stock = yf.Ticker(stock_symbol)
    stock_info = stock.info

    if data.empty or "currentPrice" not in stock_info:
        return go.Figure()

    # line_color, title = determine_color(stock_symbol)

    # ADDED FROM ACCESSIBILITY 
    current_price = stock_info.get("currentPrice", data["Close"].iloc[-1])
    prev_close = stock_info.get("previousClose", data["Close"].iloc[0])

    # Calculate price change and percentage
    price_change = current_price - prev_close
    percent_change = (price_change / prev_close) * 100

    # Determine line color
    if colorblind_mode:
        line_color = "blue" if price_change > 0 else "orange"  
    else:
        line_color = "green" if price_change > 0 else "red"
    sign = "+" if price_change > 0 else ""

    title = f"""
    {stock_info.get('shortName', stock_symbol)} <br>
    ${current_price:.2f} <span style='color:{line_color};'> <br>
    {sign}${price_change:.2f} ({sign}{percent_change:.2f}%) Today</span>
    """
    if dark_mode:
        background_color = "#141417"
        text_color       = "#dee4fc"
    else:
        background_color = "#F9F5ED"
        text_color       = "#311f6b"

    figure = go.Figure(data=[go.Scatter(
        x=data.index,
        y=data["Close"],
        mode="lines",
        line=dict(color=line_color, width=2),
        name=stock_symbol
    )])

    figure.update_layout(
        plot_bgcolor=background_color,
        paper_bgcolor=background_color,
        font=dict(color=text_color),
        title=title,
        title_x=0.5,
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True)
    )

    return figure

# 🔹 Home Route
@server.route("/", methods=["GET"])
def home():
    #stock_symbol = request.args.get("stock", "^GSPC")
    home_news = get_main_news(query="Stock Market", count=7)
    trending_stocks = get_trending_stocks(limit=10)
    return render_template("home.html", home_news=home_news, trending_stocks=trending_stocks)


# 🔹 News Page Route
@server.route('/news.html', methods=["GET", "POST"])
def news():
    if request.method == "POST":
        query = request.form.get("query", "Stock Market")
    else:
        query = request.args.get("query", "Stock Market")
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
    stock_news = get_stock_news(stock_symbol, count=4)
    ticker_news = get_latest_financial_news()
    if stock_symbol:
        stock_overview = get_stock_overview(stock_symbol)
        stock_about = get_stock_about(stock_symbol)
        trending_stocks = get_trending_stocks(limit=5)
        related_stocks = get_related_stocks(stock_symbol) # Get similar stocks for the given stock symbol
    return render_template("stock.html", stock_symbol=stock_symbol, stock_overview=stock_overview, stock_about=stock_about, trending_stocks=trending_stocks, related_stocks=related_stocks, stock_news=stock_news, ticker_news=ticker_news)

@server.route('/autocomplete_stock', methods=["GET"])
def autocomplete_stock():
    query = request.args.get("query", "").lower()
    suggestions = []

    if not query:
        return jsonify(suggestions)

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        response = requests.get(f"https://query1.finance.yahoo.com/v1/finance/search?q={query}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            for stock in data.get("quotes", [])[:10]:  # limit to 10 suggestions
                name = stock.get("shortname", stock.get("symbol"))
                symbol = stock.get("symbol")
                if name and symbol:
                    suggestions.append({"name": name, "symbol": symbol})
    except Exception as e:
        print(f"Error fetching autocomplete: {e}")

    return jsonify(suggestions)


# Run Flask + Dash
if __name__ == "__main__":
    server.run(debug=True)

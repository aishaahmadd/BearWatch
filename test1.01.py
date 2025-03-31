import yfinance as yf
from flask import Flask, render_template, request, jsonify
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objs as go

# Initialize Flask
server = Flask(__name__)

# Initialize Dash
app = Dash(__name__, server=server, routes_pathname_prefix="/dashboard/")

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


# 🔹 Dash Layout (Stock Chart)
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Graph(id="live-stock-graph"),
    dcc.Interval(id="interval-component", interval=1000, n_intervals=0)  # Auto-update every 1 second
])


# 🔹 Dash Callback (Update Stock Graph)
@app.callback(
    Output("live-stock-graph", "figure"),
    [Input("interval-component", "n_intervals"),
     Input("url", "search")]
)
def update_graph(n, search):
    stock_symbol = "^GSPC"

    if search:
        query_params = search.lstrip("?").split("&")
        params_dict = dict(param.split("=") for param in query_params if "=" in param)
        stock_symbol = params_dict.get("stock", "^GSPC")

    stock = yf.Ticker(stock_symbol)
    data = stock.history(period="1d", interval="1m")
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


# 🔹 Home Route
@server.route("/", methods=["GET"])
def home():
    stock_symbol = request.args.get("stock", "^GSPC")
    return render_template("home.html", stock_symbol=stock_symbol)


# 🔹 News Page Route
@server.route('/news.html', methods=["GET", "POST"])
def news():
    query = "Stock Market"
    if request.method == "POST":
        query = request.form.get("query")

    news_articles = get_news(query, count=8)
    return render_template("news.html", news=news_articles)

# 🔹 Stock Page Route
@server.route('/stock', methods=["GET"])
def stock():
    stock_symbol = request.args.get("stock", "^GSPC").upper()
    return render_template("stock.html", stock_symbol=stock_symbol) 


# 🔹 AJAX Route: Load More News
@server.route('/load_more_news', methods=["GET"])
def load_more_news():
    query = request.args.get("query", "Stock Market")
    offset = int(request.args.get("offset", 0))

    more_news = get_news(query, count=8, offset=offset)
    return jsonify(more_news)


# Run Flask + Dash
if __name__ == "__main__":
    server.run(debug=True)

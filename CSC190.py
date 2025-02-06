import datetime
import yfinance as yf
import time

'''
Importing stock data (Open, High, Low, Close) for userticker every 10 seconds.
Datetime from output yyyy-mm-dd hh:mm:00 DOES NOT SUPPORT SECONDS.
'''

def fetch_data(userticker: str) -> None:
    ticker = yf.Ticker(userticker)
    data = ticker.history(period="1d", interval="1m")
    print(data.tail(1))  # Display the most recent data point

# used to get current time, can be used for display
now = datetime.datetime.now()
print(now)

if __name__ == "__main__":
    while True:
        fetch_data("AAPL")
        time.sleep(10)  # Wait for 10 sec before fetching the data again
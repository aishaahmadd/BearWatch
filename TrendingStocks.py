from bs4 import BeautifulSoup
import requests

def get_trending_stocks():
    
    
    url = "https://stockanalysis.com/trending/"

    # Send an HTTP GET request to the URL
    response = requests.get(url)
    print("Response:", response)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')
    
        # Find the table or list of trending stocks
        # Trending stocks are in table rows <tr> inside <table class="table"> or similar
        table = soup.find('table')
    
        top_stocks = []
    
        if table:
            rows = table.find_all('tr')[1:]  # Skip the header row
            for row in rows[:5]:  # Get top 5
                cols = row.find_all('td')
                if len(cols) >= 2:
                    # Usually the ticker is in the second column with a link
                    ticker_tag = cols[1].find('a')
                    if ticker_tag:
                        ticker = ticker_tag.text.strip()
                        top_stocks.append(ticker)
            return top_stocks
        else:
            print("Trending stocks table not found.")
    else:
        print("Failed to retrieve the webpage.")
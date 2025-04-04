import "es6-promise/auto";

// Function to fetch news from the backend
async function fetchNews(stock: string, append: boolean = false) {
    try {
        // Make a request to the Flask backend for stock news
        const response = await fetch(`/api/news?stock=${encodeURIComponent(stock)}`);
        const newsData = await response.json();

        const newsGrid = document.getElementById("newsGrid") as HTMLDivElement;
        if (!append) newsGrid.innerHTML = "";  // Clear existing news if not appending

        if (!newsData || newsData.length === 0) {
            newsGrid.innerHTML = "<p>No news available.</p>";
            return;
        }

        // Loop through the news data and create cards for each article
        newsData.forEach((article: any) => {
            const card = document.createElement("div");
            card.className = "card";
            card.style.width = "18rem";

            // Add HTML content to the card
            card.innerHTML = `
                <img src="${article.thumbnail || 'default.jpg'}" class="card-img-top" alt="News Thumbnail">
                <div class="card-body">
                    <h5 class="card-title">${article.title}</h5>
                    <p class="card-text">${article.summary || "No summary available."}</p>
                    <a href="${article.link}" class="btn btn-primary" target="_blank">Read More</a>
                </div>
            `;
            newsGrid.appendChild(card);
        });
    } catch (error) {
        console.error("Error fetching news:", error);
    }
}

// When the page is loaded, fetch the default stock news
document.addEventListener("DOMContentLoaded", () => {
    fetchNews("AAPL");  // Default to Apple stock (AAPL)
});

// Event listener for the load more button
document.getElementById("loadMore")?.addEventListener("click", () => {
    const stockInput = (document.getElementById("stock-input") as HTMLInputElement).value || "AAPL";
    fetchNews(stockInput, true);  // Fetch more news for the given stock
});

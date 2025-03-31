import "es6-promise/auto";

async function fetchNews(stock: string, append: boolean = false) {
    try {
        const response = await fetch(`/api/news?stock=${encodeURIComponent(stock)}`);
        const newsData = await response.json();

        const newsGrid = document.getElementById("newsGrid") as HTMLDivElement;
        if (!append) newsGrid.innerHTML = "";

        if (!newsData || newsData.length === 0) {
            newsGrid.innerHTML = "<p>No news available.</p>";
            return;
        }

        newsData.forEach((article: any) => {
            const card = document.createElement("div");
            card.className = "card";
            card.style.width = "18rem";

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

document.addEventListener("DOMContentLoaded", () => {
    fetchNews("AAPL");
});

document.getElementById("loadMore")?.addEventListener("click", () => {
    const stockInput = (document.getElementById("stock-input") as HTMLInputElement).value || "AAPL";
    fetchNews(stockInput, true);
});

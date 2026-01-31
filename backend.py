import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
import urllib.parse

app = Flask(__name__)
CORS(app)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

SITES = {
    "Trendyol": "https://www.trendyol.com/sr?q={}",
    "Hepsiburada": "https://www.hepsiburada.com/ara?q={}",
    "N11": "https://www.n11.com/arama?q={}",
    "Amazon": "https://www.amazon.com.tr/s?k={}",
    "MediaMarkt": "https://www.mediamarkt.com.tr/tr/search.html?query={}",
    "Teknosa": "https://www.teknosa.com/arama/?s={}",
    "Vatan": "https://www.vatanbilgisayar.com/arama/{}"
}

def fetch(url):
    return requests.get(url, headers=HEADERS, timeout=10)

def parse(site, html):
    soup = BeautifulSoup(html, "html.parser")

    try:
        if site == "Trendyol":
            card = soup.select_one("div.p-card-wrppr")
            return {
                "url": "https://www.trendyol.com" + card.a["href"],
                "price": card.select_one("div.prc-box-dscntd").text.strip(),
                "image": card.img["src"]
            }

        if site == "Hepsiburada":
            card = soup.select_one("li.productListContent-item")
            return {
                "url": "https://www.hepsiburada.com" + card.a["href"],
                "price": card.select_one("span.price").text.strip(),
                "image": card.img["src"]
            }

        if site == "N11":
            card = soup.select_one("li.column")
            return {
                "url": card.a["href"],
                "price": card.select_one("div.priceContainer ins").text.strip(),
                "image": card.img["data-original"]
            }

        if site == "Amazon":
            card = soup.select_one("div.s-result-item")
            return {
                "url": "https://www.amazon.com.tr" + card.h2.a["href"],
                "price": card.select_one("span.a-offscreen").text.strip(),
                "image": card.img["src"]
            }

        if site == "MediaMarkt":
            card = soup.select_one("div.product-wrapper")
            return {
                "url": "https://www.mediamarkt.com.tr" + card.a["href"],
                "price": card.select_one("span.price").text.strip(),
                "image": card.img["src"]
            }

        if site == "Teknosa":
            card = soup.select_one("div.product-item")
            return {
                "url": "https://www.teknosa.com" + card.a["href"],
                "price": card.select_one("span.prc").text.strip(),
                "image": card.img["data-src"]
            }

        if site == "Vatan":
            card = soup.select_one("div.product-list__product")
            return {
                "url": "https://www.vatanbilgisayar.com" + card.a["href"],
                "price": card.select_one("span.product-list__price").text.strip(),
                "image": card.img["data-src"]
            }

    except:
        return None

@app.route("/compare", methods=["POST"])
def compare():
    data = request.json
    query = urllib.parse.quote(data.get("title", ""))

    results = []

    for site, search_url in SITES.items():
        try:
            res = fetch(search_url.format(query))
            product = parse(site, res.text)

            if product:
                results.append({
                    "site": site,
                    "price": product["price"],
                    "image": product["image"],
                    "url": product["url"]
                })
        except:
            continue

    return jsonify({"results": results})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

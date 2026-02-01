from flask import Flask, request, jsonify
from flask_cors import CORS
import urllib.parse

app = Flask(__name__)
CORS(app)

STORES = {
    "Trendyol": "https://www.trendyol.com/sr?q={}",
    "Hepsiburada": "https://www.hepsiburada.com/ara?q={}",
    "Amazon": "https://www.amazon.com.tr/s?k={}",
    "N11": "https://www.n11.com/arama?q={}",
    "Teknosa": "https://www.teknosa.com/arama/?s={}",
    "MediaMarkt": "https://www.mediamarkt.com.tr/tr/search.html?query={}",
    "Vatan": "https://www.vatanbilgisayar.com/arama/{}",
    "ÇiçekSepeti": "https://www.ciceksepeti.com/arama?query={}",
    "PttAVM": "https://www.pttavm.com/arama/{}",
    "Migros": "https://www.migros.com.tr/arama?q={}"
}

@app.route("/compare", methods=["POST"])
def compare():
    data = request.get_json()
    title = data.get("title", "")

    if not title:
        return jsonify({"results": []})

    query = urllib.parse.quote_plus(title)

    results = []
    for site, url in STORES.items():
        results.append({
            "site": site,
            "price": "Mağazada Gör",
            "image": "",
            "url": url.format(query)
        })

    return jsonify({"results": results})

@app.route("/")
def home():
    return "Fiyat Radar API Çalışıyor 🚀"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

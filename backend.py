import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
from urllib.parse import urlparse, parse_qs, unquote
import os

app = Flask(__name__)
CORS(app)

SERP_API_KEY = os.getenv("SERP_API_KEY", "BURAYA_API_KEYİNİ_YAZ")

# Google redirect link temizleyici
def clean_google_url(link):
    try:
        parsed = urlparse(link)
        qs = parse_qs(parsed.query)
        if "q" in qs:
            return unquote(qs["q"][0])
        return link
    except:
        return link

# En iyi linki seç
def extract_best_link(item):
    raw_link = (
        item.get("link") or
        item.get("product_link") or
        item.get("redirect_link") or
        ""
    )

    if not raw_link:
        return ""

    return clean_google_url(raw_link)

# Render ana sayfa kontrolü için
@app.route("/", methods=["GET"])
def home():
    return "Fiyat Radarı Backend Çalışıyor", 200

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        search_query = data.get("title", "")

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr",
            "gl": "tr"
        }

        response = requests.get("https://serpapi.com/search.json", params=params, timeout=20)
        results = response.json().get("shopping_results", [])

        output = []
        for item in results[:10]:
            clean_link = extract_best_link(item)

            product_id = ""
            id_match = re.search(r'p-(\d+)|/(\d{7,})', clean_link)
            if id_match:
                product_id = id_match.group(1) or id_match.group(2)

            output.append({
                "site": item.get("source", ""),
                "price": item.get("price", ""),
                "image": item.get("thumbnail", ""),
                "p_id": product_id,
                "title": item.get("title", ""),
                "url": clean_link
            })

        return jsonify({"results": output})

    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

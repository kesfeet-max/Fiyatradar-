import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"


# -----------------------------
# Ana sayfa (Render için 404 yerine 200 dönsün)
# -----------------------------
@app.route("/", methods=["GET"])
def home():
    return "Fiyat Radarı Backend Çalışıyor", 200


# -----------------------------
# Google Shopping arama
# -----------------------------
def search_product(query):
    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": SERP_API_KEY,
        "hl": "tr",
        "gl": "tr"
    }

    r = requests.get("https://serpapi.com/search.json", params=params, timeout=15)
    data = r.json()

    results = data.get("shopping_results", [])
    if not results:
        return None

    return results[0]


# -----------------------------
# Satıcı linklerini çek
# -----------------------------
def get_offers(immersive_api_url):
    r = requests.get(immersive_api_url, timeout=15)
    data = r.json()

    offers = data.get("offers", [])
    output = []

    for offer in offers:
        merchant = offer.get("merchant", {})
        output.append({
            "site": merchant.get("name", ""),
            "price": offer.get("price", ""),
            "url": offer.get("link", ""),
            "image": offer.get("thumbnail", "")
        })

    return output


# -----------------------------
# API Endpoint
# -----------------------------
@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        query = data.get("title", "")

        if not query:
            return jsonify({"results": [], "error": "Ürün adı boş"}), 400

        product = search_product(query)
        if not product:
            return jsonify({"results": [], "error": "Ürün bulunamadı"}), 404

        immersive_api = product.get("serpapi_immersive_product_api")
        if not immersive_api:
            return jsonify({"results": [], "error": "Satıcı bilgisi yok"}), 404

        offers = get_offers(immersive_api)

        return jsonify({
            "product": {
                "title": product.get("title", ""),
                "image": product.get("thumbnail", "")
            },
            "results": offers
        })

    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500


# -----------------------------
# Lokal çalıştırma
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

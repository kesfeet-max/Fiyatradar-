import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

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

    return results[0]  # En üstteki ürünü alıyoruz


# -----------------------------
# Satıcı linklerini çek
# -----------------------------
def get_offers(immersive_api_url):
    r = requests.get(immersive_api_url, timeout=15)
    data = r.json()

    offers = data.get("offers", [])
    output = []

    for offer in offers:
        output.append({
            "site": offer.get("merchant", {}).

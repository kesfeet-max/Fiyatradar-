import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
from urllib.parse import urlparse, parse_qs, unquote

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_google_url(link):
    try:
        parsed = urlparse(link)
        qs = parse_qs(parsed.query)
        if "q" in qs:
            return unquote(qs["q"][0])
        return link
    except:
        return link

def extract_best_link(item):
    """
    SerpAPI farklı alanlarda link döndürüyor
    Öncelik sırası:
    1. link
    2. product_link
    3. redirect_link
    """
    raw_link = (
        item.get("link") or
        item.get("product_link") or
        item.get("redirect_link") or
        ""
    )

    if not raw_link:
        return ""

    return clean_google_url(raw_link)

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

        response = requests.get("https://serpapi.com/search.json", params=params)
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
                "title": item.get("title

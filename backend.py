import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_price(price_str):
    if not price_str: return 0.0
    try:
        cleaned = str(price_str).replace('TL', '').replace(' ', '').replace('.', '').replace(',', '.')
        return float(re.sub(r'[^\d.]', '', cleaned))
    except: return 0.0

@app.route("/compare", methods=["POST"])
def compare():
    data = request.get_json()
    full_title = data.get("title", "")
    current_page_price = clean_price(data.get("original_price", "0"))
    
    search_query = " ".join(full_title.split()[:5]) 

    params = {
        "engine": "google_shopping",
        "q": search_query,
        "hl": "tr",
        "gl": "tr",
        "api_key": SERP_API_KEY
    }

    try:
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=20)
        results = response.json().get("shopping_results", [])
    except:
        return jsonify({"results": []})

    final_results = []
    for item in results:
        price_val = clean_price(item.get("price"))
        # Sadece ucuz olanlar
        if current_page_price > 0 and price_val >= current_page_price:
            continue
        
        # LINK TAMİRİ: Eğer link yoksa ürünü listeye bile ekleme!
        item_link = item.get("link")
        if not item_link or not str(item_link).startswith("http"):
            continue

        final_results.append({
            "site": item.get("source", "Mağaza"),
            "price": item.get("price"),
            "link": item_link, # Temizlenmiş ve doğrulanmış link
            "p_val": price_val
        })

    # En ucuz en üstte
    sorted_results = sorted(final_results, key=lambda x: x['p_val'])
    return jsonify({"results": sorted_results[:8]})

if __name__ == "__main__":
    app.run()

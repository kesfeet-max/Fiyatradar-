import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_price(price_str):
    try:
        # '35.499 TL' gibi metinleri sayıya çevirir
        cleaned = re.sub(r'[^\d,]', '', str(price_str)).replace(',', '.')
        return float(cleaned)
    except: return 0.0

@app.route("/compare", methods=["POST"])
def compare():
    data = request.get_json()
    full_title = data.get("title", "")
    current_price = clean_price(data.get("original_price", "0")) # Sayfadaki fiyat
    
    # Arama sorgusunu optimize et
    search_query = " ".join(full_title.split()[:5]) 

    params = {
        "engine": "google_shopping",
        "q": search_query,
        "hl": "tr", "gl": "tr",
        "api_key": SERP_API_KEY
    }

    try:
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=25)
        shopping_results = response.json().get("shopping_results", [])
    except: return jsonify({"results": []})

    cheap_results = []
    # Güvenilir TR siteleri
    whitelist = ["trendyol", "hepsiburada", "n11", "amazon", "vatan", "teknosa", "pazarama", "ciceksepeti", "idefix", "mediamarkt"]

    for item in shopping_results:
        site = item.get("source", "").lower()
        found_price_val = clean_price(item.get("price", "0"))
        link = item.get("link", "")

        # KRİTİK FİLTRE: Sadece sayfadaki fiyattan ucuz olanları al
        # (Eğer ürün 35.499 ise, 35.400 ve altını gösterir)
        if current_price > 0 and found_price_val >= current_price:
            continue

        # TR sitesi kontrolü
        if any(w in site for w in whitelist) or ".tr" in link.lower():
            cheap_results.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": link,
                "price_num": found_price_val
            })

    # En ucuzu en üste koy
    sorted_list = sorted(cheap_results, key=lambda x: x['price_num'])
    for item in sorted_list: del item['price_num']

    return jsonify({"results": sorted_list})

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_price(price_str):
    try:
        # Fiyatı sayıya çevirir: '46.796,84 TL' -> 46796.84
        cleaned = re.sub(r'[^\d,]', '', str(price_str)).replace(',', '.')
        return float(cleaned)
    except: return 0.0

@app.route("/compare", methods=["POST"])
def compare():
    data = request.get_json()
    full_title = data.get("title", "")
    orig_price_str = data.get("original_price", "0")
    base_price = clean_price(orig_price_str)

    # Aramayı sadeleştiriyoruz ki Google daha çok ucuz seçenek bulsun
    search_query = " ".join(full_title.split()[:5]) 

    params = {
        "engine": "google_shopping",
        "q": search_query,
        "hl": "tr", "gl": "tr",
        "api_key": SERP_API_KEY
    }

    try:
        response = requests.get("https://serpapi.com/search.json", params=params)
        shopping_results = response.json().get("shopping_results", [])
    except: return jsonify({"results": []})

    cheap_results = []
    # Sadece Türkiye siteleri
    whitelist = ["trendyol", "hepsiburada", "n11", "amazon", "vatan", "teknosa", "pazarama", "ciceksepeti", "vatanbilgisayar"]

    for item in shopping_results:
        site = item.get("source", "").lower()
        price_val = clean_price(item.get("price", "0"))
        link = item.get("link")

        # FİLTRE: Eğer bulduğumuz fiyat, senin baktığın fiyattan ucuzsa veya 
        # çok küçük bir fark varsa listeye alıyoruz. Pahalı olanları eliyoruz.
        # (base_price * 1.02) -> Senin fiyatından %2'den daha pahalı olanları göstermez.
        if base_price > 0 and price_val > (base_price * 1.02):
            continue 

        if any(w in site for w in whitelist) or ".tr" in link.lower():
            cheap_results.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": link,
                "price_num": price_val
            })

    # En ucuzu en tepeye koy
    sorted_results = sorted(cheap_results, key=lambda x: x['price_num'])
    for item in sorted_results: del item['price_num']

    return jsonify({"results": sorted_results})

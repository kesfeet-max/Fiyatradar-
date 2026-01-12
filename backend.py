import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_price(price_str):
    try:
        # Fiyatı sayıya çevirir (Örn: 35.499 TL -> 35499.0)
        cleaned = re.sub(r'[^\d,]', '', str(price_str)).replace(',', '.')
        return float(cleaned)
    except: return 0.0

@app.route("/compare", methods=["POST"])
def compare():
    data = request.get_json()
    full_title = data.get("title", "")
    # Mevcut sayfanın fiyatını alıyoruz
    current_page_price = clean_price(data.get("original_price", "0"))
    
    # Arama terimini sadeleştir (İlk 5 kelime)
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
    whitelist = ["trendyol", "hepsiburada", "n11", "amazon", "vatan", "teknosa", "pazarama", "ciceksepeti", "mediamarkt"]

    for item in shopping_results:
        site = item.get("source", "").lower()
        found_price_val = clean_price(item.get("price", "0"))
        link = item.get("link", "")

        # FİLTRE: Sadece senin fiyatından DAHA UCUZ olanları listeye al
        if current_page_price > 0 and found_price_val >= current_page_price:
            continue

        if any(w in site for w in whitelist) or ".tr" in link.lower():
            cheap_results.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": link,
                "price_num": found_price_val
            })

    # En ucuzdan pahalıya sırala
    sorted_list = sorted(cheap_results, key=lambda x: x['price_num'])
    for item in sorted_list: del item['price_num']

    return jsonify({"results": sorted_list})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

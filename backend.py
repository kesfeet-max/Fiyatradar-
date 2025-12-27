import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_price(price_str):
    try:
        cleaned = re.sub(r'[^\d,]', '', str(price_str)).replace(',', '.')
        return float(cleaned)
    except: return 0.0

@app.route("/compare", methods=["POST"])
def compare():
    data = request.get_json()
    full_title = data.get("title", "")
    
    # Arama terimini optimize et (Çok uzun başlıklar sonuç vermez)
    search_query = " ".join(full_title.split()[:6]) 

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

    final_results = []
    # Yasaklı (TR dışı) kelimeler
    blacklist = ["microless", "desertcart", "ubuy", "ebay", "aliexpress", "u-buy"]

    for item in shopping_results:
        site = item.get("source", "").lower()
        price_val = clean_price(item.get("price", "0"))
        link = item.get("link", "")

        # Yabancı siteleri engelle
        if any(bad in site for bad in blacklist): continue
        
        # Sadece Türkiye odaklı sonuçları ekle
        if ".tr" in link or any(tr in site for tr in ["trendyol", "hepsiburada", "n11", "amazon", "vatan", "teknosa", "pazarama", "ciceksepeti", "idefix"]):
            final_results.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": link,
                "price_num": price_val
            })

    # En ucuza göre sırala (Senin istediğin gibi ucuzlar en üstte)
    sorted_list = sorted(final_results, key=lambda x: x['price_num'])
    for item in sorted_list: del item['price_num']

    return jsonify({"results": sorted_list})

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def parse_price(price_str):
    if not price_str: return 0
    try:
        val = re.sub(r'[^\d]', '', str(price_str).split(',')[0])
        return int(val)
    except: return 0

@app.route("/", methods=["GET"])
def home():
    return "FiyatBul API Calisiyor!", 200

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        original_title = data.get("title", "").lower()
        current_price = parse_price(data.get("price", "0"))
        
        # Arama sorgusunu daraltıyoruz
        search_query = " ".join(original_title.split()[:5])

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "num": "30"
        }

        results = requests.get("https://serpapi.com/search.json", params=params).json().get("shopping_results", [])
        
        final_list = []
        # AKSESUAR VE YEDEK PARÇA FİLTRESİ
        forbidden = ["tel", "izgara", "yedek", "parça", "aksesuar", "kılıf", "cam", "ikinci el", "dvd", "kitap"]

        for item in results:
            item_title = item.get("title", "").lower()
            item_price = parse_price(item.get("price"))
            
            # 1. Filtre: Fiyat aşırı düşükse (ana ürünün %60'ından azsa) kesin yedek parçadır, ELE.
            if current_price > 0 and item_price < (current_price * 0.6):
                continue

            # 2. Filtre: Yasaklı kelime kontrolü
            if any(f in item_title for f in forbidden) and not any(f in original_title for f in forbidden):
                continue

            final_list.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": item.get("link") or item.get("product_link"),
                "raw_price": item_price
            })
        
        final_list.sort(key=lambda x: x['raw_price'])
        return jsonify({"results": final_list[:8]})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

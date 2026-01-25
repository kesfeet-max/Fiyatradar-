import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

@app.route("/", methods=["GET"])
def home():
    return "Fiyat Bul Sunucusu Calisiyor!", 200

def parse_price(price_str):
    if not price_str: return 0
    try:
        # Fiyatı sayıya çevirir (Örn: "3.260,40 TL" -> 3260)
        val = re.sub(r'[^\d]', '', str(price_str).split(',')[0])
        return int(val)
    except: return 0

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"results": [], "error": "Veri gonderilmedi"}), 400
            
        original_title = data.get("title", "").strip()
        # Eklentiden gelen o anki sayfa fiyatı
        current_page_price = parse_price(data.get("price", "0"))
        
        # Arama sorgusu
        search_words = original_title.lower().split()[:4]
        search_query = " ".join(search_words)

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr",
            "num": "30"
        }

        response = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        forbidden = ["dvd", "2.el", "ikinci el", "kullanılmış", "tek kitap", "parça"]

        for item in results:
            item_title = item.get("title", "").lower()
            item_price = parse_price(item.get("price"))
            
            # --- GELİŞMİŞ FİLTRELEME ---
            
            # 1. Fiyat Koruma: Aranan üründen %50 daha ucuz olanları gösterme (Kitap/DVD ayrımı)
            if current_page_price > 0:
                if item_price < (current_page_price * 0.6): # Örn: 3000 TL ürün için 1800 TL altını eler
                    continue

            # 2. Marka Kontrolü: İlk iki kelime mutlaka başlıkta geçmeli
            is_match = all(word in item_title for word in search_words[:2])
            
            if is_match and not any(f in item_title for f in forbidden):
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

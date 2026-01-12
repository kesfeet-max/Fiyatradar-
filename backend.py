import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

# Flask uygulamasını başlatıyoruz
app = Flask(__name__)
CORS(app)

# Senin SerpApi Anahtarın
SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

@app.route("/", methods=["GET", "HEAD"])
def home():
    return "Fiyat Radarı Sunucusu Aktif!"

def clean_price(price_str):
    if not price_str: return 0.0
    try:
        cleaned = str(price_str).replace('TL', '').replace('₺', '').replace(' ', '')
        if ',' in cleaned and '.' in cleaned:
            cleaned = cleaned.replace('.', '')
        cleaned = cleaned.replace(',', '.')
        return float(re.sub(r'[^\d.]', '', cleaned))
    except:
        return 0.0

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        full_title = data.get("title", "")
        # Aramayı hızlandırmak için sadece ilk 3 kelimeyi alıyoruz
        search_query = " ".join(full_title.split()[:3]) 
        current_price = clean_price(data.get("original_price", "0"))

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "hl": "tr",
            "gl": "tr",
            "api_key": SERP_API_KEY
        }

        # Google'dan verileri çek (Zaman aşımı 8 saniye - Hız için)
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=8)
        results = response.json().get("shopping_results", [])
        
        cheap_results = []
        # En popüler ve güvenilir mağazalar
        whitelist = ["trendyol", "hepsiburada", "n11", "amazon", "vatan", "teknosa"]

        for item in results:
            source = item.get("source", "").lower()
            price_val = clean_price(item.get("price"))
            link = item.get("link")

            if any(w in source for w in whitelist) and link:
                if current_price == 0 or price_val < current_price:
                    cheap_results.append({
                        "site": item.get("source"),
                        "price": item.get("price"),
                        "link": link,
                        "p_val": price_val
                    })
        
        # En ucuzu başa getir
        sorted_results = sorted(cheap_results, key=lambda x: x['p_val'])
        for x in sorted_results: del x['p_val']

        return jsonify({"results": sorted_results[:6]})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    app.run()

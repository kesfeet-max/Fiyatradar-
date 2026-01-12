import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

# Render loglarında 404 almamak için app isminin doğruluğundan emin olun
app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

@app.route("/", methods=["GET", "HEAD"])
def home():
    # Loglardaki 404 hatasını bu satır çözer
    return "Fiyat Radarı Sunucusu Aktif!"

def clean_price(price_str):
    if not price_str: return 0.0
    try:
        # Screenshot_80'deki 4.293,45 TL formatını temizler
        cleaned = str(price_str).replace('TL', '').replace('₺', '').replace(' ', '')
        if ',' in cleaned and '.' in cleaned:
            cleaned = cleaned.replace('.', '')
        cleaned = cleaned.replace(',', '.')
        return float(re.sub(r'[^\d.]', '', cleaned))
    except:
        return 0.0

@app.route("/compare", methods=["POST"])
def compare():
    data = request.get_json()
    # Eklentiden gelen başlığı al
    full_title = data.get("title", "")
    current_price = clean_price(data.get("original_price", "0"))
    
    # Screenshot_90'daki uzun aramayı kısalt: İlk 3 kelime en iyi sonucu verir
    search_query = " ".join(full_title.split()[:3]) 

    params = {
        "engine": "google_shopping",
        "q": search_query,
        "hl": "tr",
        "gl": "tr",
        "api_key": SERP_API_KEY
    }

    try:
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=15)
        api_data = response.json()
        results = api_data.get("shopping_results", [])
        
        # Eğer API boş dönüyorsa (Loglardaki 15 bayt sorunu)
        if not results:
             return jsonify({"results": [
                {"site": "Google Arama", "price": "Sonuçlar için tıkla", "link": f"https://www.google.com/search?q={search_query}+fiyat"}
            ]})

    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

    cheap_results = []
    whitelist = ["trendyol", "hepsiburada", "n11", "amazon", "vatan", "teknosa", "pazarama"]

    for item in results:
        price_val = clean_price(item.get("price"))
        source = item.get("source", "").lower()
        link = item.get("link")

        if any(w in source for w in whitelist):
            # Fiyat okunamasa bile (0 ise) sonuçları göster
            if current_price == 0 or price_val < current_price:
                cheap_results.append({
                    "site": item.get("source"),
                    "price": item.get("price"),
                    "link": link,
                    "p_val": price_val
                })

    sorted_results = sorted(cheap_results, key=lambda x: x['p_val'])
    for x in sorted_results: del x['p_val']
    
    # Yanıtın boş gitmediğinden emin ol
    return jsonify({"results": sorted_results[:8]})

if __name__ == "__main__":
    app.run()

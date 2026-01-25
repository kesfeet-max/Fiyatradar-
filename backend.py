import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os
from urllib.parse import urlparse, parse_qs, unquote

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def parse_price(price_str):
    """Fiyat metnini sayıya çevirir."""
    if not price_str: return 0
    try:
        # '₺295,00' -> '295'
        val = re.sub(r'[^\d]', '', str(price_str).split(',')[0])
        return int(val)
    except:
        return 0

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        original_title = data.get("title", "").lower()
        
        # Daha geniş sonuç için 3-4 kelimeye düşürelim
        search_query = " ".join(original_title.split()[:4])

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr",
            "gl": "tr"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        for item in results:
            # 1. LINK TEMIZLEME
            raw_link = item.get("direct_link") or item.get("link") or ""
            
            if "url?q=" in raw_link:
                raw_link = raw_link.split("url?q=")[1].split("&")[0]
            elif "adurl=" in raw_link:
                raw_link = raw_link.split("adurl=")[1].split("&")[0]
            
            clean_url = unquote(raw_link)
            
            # 2. FIYAT ANALIZI
            item_price = parse_price(item.get("price"))

            final_list.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": clean_url,
                "image": item.get("thumbnail"),
                "raw_price": item_price
            })
        
        # En ucuzdan pahalıya sırala
        final_list.sort(key=lambda x: x['raw_price'])
        
        return jsonify({"results": final_list[:10]})

    except Exception as e:
        print(f"Hata oluştu: {str(e)}") # Loglarda hatayı görmek için
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

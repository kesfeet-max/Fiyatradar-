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
    if not price_str: return 0
    try:
        # Fiyattaki gereksiz karakterleri temizler (₺, . , vb.)
        val = re.sub(r'[^\d]', '', str(price_str).split(',')[0])
        return int(val)
    except:
        return 0

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        # Alakasız ürünleri engellemek için başlığı olduğu gibi kullanıyoruz
        original_title = data.get("title", "")
        
        params = {
            "engine": "google_shopping",
            "q": original_title,
            "api_key": SERP_API_KEY,
            "hl": "tr",
            "gl": "tr",
            "num": "15" # Daha fazla sonuç arasından en iyileri seçmek için
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        shopping_results = response.json().get("shopping_results", [])
        
        final_list = []
        for item in shopping_results:
            # Google sarmalından kurtulmak için en temiz linki seç
            link = item.get("direct_link") or item.get("link") or ""
            
            # Link temizleme işlemi
            if "url?q=" in link:
                link = link.split("url?q=")[1].split("&")[0]
            elif "adurl=" in link:
                link = link.split("adurl=")[1].split("&")[0]

            final_list.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": unquote(link),
                "image": item.get("thumbnail"),
                "raw_price": parse_price(item.get("price"))
            })
        
        # En ucuz fiyatı başa getir
        final_list.sort(key=lambda x: x['raw_price'])
        
        return jsonify({"results": final_list[:10]})

    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def format_price(price_str):
    if not price_str: return 0
    try:
        cleaned = re.sub(r'[^\d]', '', str(price_str).split(',')[0])
        return int(cleaned)
    except: return 0

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        full_title = data.get("title", "")
        # Aramayı daha esnek bırakıyoruz ki 112.000 TL'lik alternatifler gelsin
        search_query = " ".join(full_title.split()[:4])

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr",
            "num": "40" # Tarama sayısını artırdık
        }

        response = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        # Sadece kılıf ve cam gibi net aksesuarları eliyoruz
        forbidden = ["kılıf", "case", "cam", "film", "kapak", "yedek", "parça", "tamir"]
        
        for item in results:
            title = item.get("title", "").lower()
            price_val = format_price(item.get("price"))
            link = item.get("link") or item.get("product_link")

            # Fiyat 5000 TL üstündeyse gerçek üründür
            if not any(word in title for word in forbidden) and price_val > 5000:
                final_list.append({
                    "site": item.get("source"),
                    "price": item.get("price"),
                    "link": link,
                    "raw_price": price_val
                })
        
        # En ucuz olanı en başa al
        final_list.sort(key=lambda x: x['raw_price'])

        return jsonify({"results": final_list[:10]}) 
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    app.run()

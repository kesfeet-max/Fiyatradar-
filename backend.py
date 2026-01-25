import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        title = data.get("title", "")
        
        params = {
            "engine": "google_shopping",
            "q": title,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        for item in results:
            # Sadece sayısal fiyatı al
            price_str = item.get("price", "0")
            raw_price = int(re.sub(r'[^\d]', '', price_str.split(',')[0])) if price_str else 0

            final_list.append({
                "site": item.get("source"),
                "price": price_str,
                "title": item.get("title"), # Ürün adını da gönderiyoruz
                "link": item.get("direct_link") or item.get("link") or "",
                "image": item.get("thumbnail"),
                "raw_price": raw_price
            })
        
        final_list.sort(key=lambda x: x['raw_price'])
        return jsonify({"results": final_list[:10]})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

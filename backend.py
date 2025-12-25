import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_price(price_str):
    try:
        cleaned = re.sub(r'[^\d,]', '', str(price_str)).replace(',', '.')
        return float(cleaned)
    except:
        return 0.0

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return "", 200
    
    data = request.get_json(silent=True) or {}
    title = data.get("title", "")
    orig_price_str = data.get("original_price", "0")
    base_price = clean_price(orig_price_str)

    search_query = ' '.join(title.split()[:5])
    
    params = {
        "engine": "google_shopping",
        "q": search_query,
        "hl": "tr",
        "gl": "tr",
        "api_key": SERP_API_KEY
    }

    try:
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=15)
        shopping_results = response.json().get("shopping_results", [])
        
        final_results = []
        forbidden = ["yedek", "parça", "filtre", "deterjan", "hortum", "aparat", "başlık", "aksesuar"]

        for item in shopping_results[:20]:
            # n11 hatasını önlemek için doğrudan linki alıyoruz
            actual_link = item.get("link") or item.get("product_link")
            if not actual_link: continue

            item_price = clean_price(item.get("price", "0"))
            item_title = item.get("title", "").lower()
            
            # Filtreleme: Fiyat %30'un altındaysa veya yasaklı kelime varsa ele
            is_accessory = any(word in item_title for word in forbidden)
            is_too_cheap = item_price < (base_price * 0.3) if base_price > 0 else False
            
            if not is_accessory and not is_too_cheap:
                final_results.append({
                    "title": item.get("title", ""),
                    "site": item.get("source", "Satıcı"),
                    "price": item.get("price", "Fiyat Yok"),
                    "link": actual_link 
                })

        return jsonify({"results": final_results[:10]}) 
    except:
        return jsonify({"results": []}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

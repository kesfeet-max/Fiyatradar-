import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_price(price_str):
    """Metin halindeki fiyatı sayıya çevirir: '4.199 TL' -> 4199.0"""
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

    # Arama terimini optimize et (Model adını kapsayacak şekilde ilk 5 kelime)
    search_query = ' '.join(title.split()[:5])
    
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_shopping",
        "q": search_query,
        "hl": "tr",
        "gl": "tr",
        "api_key": SERP_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        shopping_results = response.json().get("shopping_results", [])
        
        final_results = []
        # Yedek parça kirliliğini temizleyen liste
        forbidden = ["yedek", "parça", "filtre", "deterjan", "hortum", "başlık", "aksesuar"]

        for item in shopping_results[:20]:
            # Link hatasını çözmek için hiyerarşik link kontrolü
            actual_link = item.get("link") or item.get("product_link")
            
            if not actual_link:
                continue

            item_price = clean_price(item.get("price", "0"))
            item_title = item.get("title", "").lower()
            
            # Akıllı Filtreleme
            is_accessory = any(word in item_title for word in forbidden)
            is_too_cheap = item_price < (base_price * 0.4) if base_price > 0 else False
            
            if not is_accessory and not is_too_cheap:
                final_results.append({
                    "title": item.get("title", ""),
                    "site": item.get("source", "Satıcı"),
                    "price": item.get("price", "Fiyat Yok"),
                    "link": actual_link 
                })

        return jsonify({"results": final_results[:10]}) 
    except Exception as e:
        print(f"Hata oluştu: {e}")
        return jsonify({"results": []}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

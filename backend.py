import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def get_real_prices_with_api(product_name):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_shopping",
        "q": product_name, # Tırnak işaretlerini kaldırdık, daha çok sonuç için
        "hl": "tr",
        "gl": "tr",
        "api_key": SERP_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        shopping_results = data.get("shopping_results", [])
        
        results = []
        # 20 sonucu geri getirdik
        for item in shopping_results[:20]:
            # Boş Google sayfasına gitmemesi için link hiyerarşisini düzelttik
            actual_link = item.get("link") or item.get("product_link") or item.get("serpapi_product_api_cx")
            
            if actual_link and actual_link != "#":
                results.append({
                    "site": item.get("source", "Satıcı"),
                    "price": item.get("price", "Fiyat Yok"),
                    "link": actual_link 
                })
        return results
    except Exception as e:
        return []

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return "", 200
    data = request.get_json(silent=True) or {}
    title = data.get("title", "")
    
    # Arama terimini optimize et (Model adını koruyarak ilk 4 kelime)
    search_title = ' '.join(title.split()[:4])
    
    results = get_real_prices_with_api(search_title)
    return jsonify({"query": search_title, "results": results}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

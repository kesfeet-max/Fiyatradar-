import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# 🔑 SerpApi Anahtarın
SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def get_real_prices_with_api(product_name):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_shopping",
        "q": product_name,
        "hl": "tr",
        "gl": "tr",
        "api_key": SERP_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        shopping_results = data.get("shopping_results", [])
        
        results = []
        for item in shopping_results[:20]:
            # 🚀 Link Sorununu Çözen Kısım: Farklı link türlerini kontrol ediyoruz
            actual_link = item.get("link") or item.get("product_link") or "#"
            
            results.append({
                "site": item.get("source", "Satıcı"),
                "price": item.get("price", "Fiyat Yok"),
                "link": actual_link 
            })
        return results
    except Exception as e:
        print(f"Hata: {e}")
        return []

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json(silent=True) or {}
    title = data.get("title", "")
    
    # Arama terimini optimize et (ilk 5 kelime)
    search_title = ' '.join(title.split()[:5])
    
    # API'den sonuçları çek
    results = get_real_prices_with_api(search_title)
    
    if not results:
        results = [{"site": "Bilgi", "price": "Sonuç bulunamadı", "link": "#"}]

    return jsonify({
        "query": search_title,
        "results": results
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)


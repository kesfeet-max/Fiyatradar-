import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# SerpApi'den aldığın anahtarı buraya tırnak içine yapıştır
SERP_API_KEY = "d43c689b60f306d44001fdc112fb5ed4ba69163a82ba87dac55b78c2a7449950"

def get_real_prices_with_api(product_name):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_shopping",
        "q": f"{product_name} fiyatı",
        "hl": "tr",
        "gl": "tr",
        "api_key": SERP_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        # Alışveriş sonuçlarını alıyoruz
        shopping_results = data.get("shopping_results", [])
        
        results = []
        for item in shopping_results[:3]: # En ucuz 3 sonuç
            results.append({
                "site": item.get("source", "Bilinmeyen Site"),
                "price": item.get("price", "Fiyat Yok"),
                "link": item.get("link", "#")
            })
        return results
    except Exception as e:
        print(f"API Hatası: {e}")
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
    
    # Arama terimini sadeleştir (Model adını al)
    search_title = ' '.join(title.split()[:4])
    
    results = get_real_prices_with_api(search_title)
    
    if not results:
        results = [{"site": "Bilgi", "price": "Sonuç bulunamadı", "link": "#"}]

    return jsonify({
        "query": search_title,
        "results": results
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

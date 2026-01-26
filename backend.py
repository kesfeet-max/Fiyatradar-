import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        original_title = data.get("title", "")
        
        # Filtreleme için model kodlarını koru ama gereksiz ekleri temizle
        clean_search = " ".join(original_title.split()[:6])

        params = {
            "engine": "google_shopping",
            "q": clean_search,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        for item in results:
            # SADECE VERİ GÖNDERİYORUZ, GOOGLE LİNKİ GÖNDERMİYORUZ
            final_list.append({
                "site": item.get("source", ""),
                "price": item.get("price"),
                "image": item.get("thumbnail"),
                "title": item.get("title") # Mağaza içinde nokta atışı arama için
            })
        
        return jsonify({"results": final_list[:10]})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

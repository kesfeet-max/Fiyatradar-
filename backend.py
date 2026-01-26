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
        
        params = {
            "engine": "google_shopping",
            "q": original_title,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "num": "10"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        for item in results:
            source = item.get("source", "").lower()
            # Google'ın verdiği bozuk linki alıyoruz
            raw_link = item.get("link", "")
            
            # Ürün ID'sini SerpApi'nin sağladığı diğer alanlardan çekmeye çalışıyoruz
            # Eğer doğrudan link temizlenemezse eklenti 'title' üzerinden gidecek
            product_id = item.get("product_id", "") 

            final_list.append({
                "site": item.get("source", "Mağaza"),
                "price": item.get("price"),
                "image": item.get("thumbnail"),
                "link": raw_link,
                "product_id": product_id,
                "title": item.get("title") # Arama için temiz başlık
            })
        
        return jsonify({"results": final_list})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

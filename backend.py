import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        full_title = data.get("title", "")
        # Aramayı stabilize etmek için ilk 3 kelimeyi alıyoruz
        search_query = " ".join(re.sub(r'[^\w\s]', '', full_title).split()[:3])

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr"
        }

        response = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        results = response.json().get("shopping_results", [])
        
        final_results = []
        whitelist = ["trendyol", "hepsiburada", "n11", "amazon", "vatan", "teknosa", "pazarama"]

        for item in results:
            source = item.get("source", "").lower()
            # ÖNEMLİ: Linkin varlığını ve doğruluğunu burada garantiye alıyoruz
            direct_link = item.get("link") or item.get("product_link") or item.get("shopping_results_link")
            
            if any(w in source for w in whitelist) and direct_link:
                final_results.append({
                    "site": item.get("source"),
                    "price": item.get("price"),
                    "link": direct_link # Link burada mutlaka tanımlanıyor
                })
        
        return jsonify({"results": final_results[:6]})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    app.run()

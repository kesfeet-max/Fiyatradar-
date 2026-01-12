import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

@app.route("/", methods=["GET", "HEAD"])
def home():
    return "Fiyat Radarı Sistemi Aktif!"

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        full_title = data.get("title", "")
        
        # CİMRİ MANTIĞI: Başlıktaki marka ve model dışındaki gereksiz kelimeleri atıyoruz
        # Sadece ilk 3 kelime ile arama yaparak Google'dan sonuç gelmesini garanti ediyoruz.
        clean_query = re.sub(r'[^\w\s]', '', full_title).split()
        search_query = " ".join(clean_query[:3]) 

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "hl": "tr", "gl": "tr",
            "api_key": SERP_API_KEY
        }

        # Render zaman aşımını önlemek için hızlı cevap istiyoruz
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        whitelist = ["trendyol", "hepsiburada", "n11", "amazon", "vatan", "teknosa", "pazarama"]

        for item in results:
            source = item.get("source", "").lower()
            if any(w in source for w in whitelist):
                final_list.append({
                    "site": item.get("source"),
                    "price": item.get("price"),
                    "link": item.get("link")
                })
        
        return jsonify({"results": final_list[:6]})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    app.run()

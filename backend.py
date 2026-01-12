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
        
        # HATA DÜZELTME: Sadece ilk 3-4 kelimeyi alarak arama yapmak bazen alakasız sonuç döndürür.
        # "Poco F8 Pro" gibi kritik kelimeleri koruyup, gereksiz ekleri (Ram, Hafıza vb.) temizliyoruz.
        search_query = " ".join(full_title.split()[:5]) 

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr",
            "gl": "tr",
            "num": "15" # Daha fazla sonuç çekip içinden doğru olanları seçeceğiz
        }

        response = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        results = response.json().get("shopping_results", [])
        
        final_results = []
        whitelist = ["trendyol", "hepsiburada", "n11", "amazon", "vatan", "teknosa", "pazarama"]

        # ALAKASIZ ÜRÜN FİLTRESİ
        main_keyword = search_query.split()[0].lower() # Örn: "Poco"

        for item in results:
            source = item.get("source", "").lower()
            title = item.get("title", "").lower()
            link = item.get("link") or item.get("product_link") or item.get("shopping_results_link")
            
            # Eğer ürün başlığında aradığımız ana marka/kelime yoksa (Poco bakarken Roborock gelmesi gibi) eliyoruz
            if main_keyword in title and any(w in source for w in whitelist) and link:
                final_results.append({
                    "site": item.get("source"),
                    "price": item.get("price"),
                    "link": link
                })
        
        return jsonify({"results": final_results[:6]})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    app.run()

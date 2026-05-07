import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_price(price_str):
    if not price_str or price_str == "0": return 0
    try:
        s = str(price_str).replace('TL', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        s = re.sub(r'[^\d.]', '', s)
        return float(s)
    except:
        return 0

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200
    try:
        data = request.get_json()
        title = data.get("title", "")
        # Eklentiden gelen fiyatı al
        current_price = clean_price(data.get("price", "0"))
        
        params = {
            "engine": "google_shopping",
            "q": title,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "direct_link": True
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        for item in results:
            p_val = clean_price(item.get("price", "0"))
            
            # --- %100 KESİN FİLTRE ---
            # Eğer ürün 50.000 TL'den pahalıysa (Robot süpürge için bu imkansız), ASLA GÖSTERME.
            if p_val > 50000:
                continue

            # Eğer ana fiyatı okuyabildiysek, onun %50 fazlasından pahalı olanı GÖSTERME.
            if current_price > 0 and p_val > (current_price * 1.5):
                continue
            
            final_list.append({
                "site": item.get("source", "Mağaza"),
                "price": item.get("price"),
                "price_value": p_val,
                "image": item.get("thumbnail"),
                "link": item.get("link", ""),
                "title": item.get("title")
            })
        
        final_list.sort(key=lambda x: x['price_value'] if x['price_value'] > 0 else 999999)
        return jsonify({"results": final_list})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

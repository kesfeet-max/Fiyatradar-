import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_price(price_str):
    if not price_str: return 0
    try:
        # Sayı dışındaki her şeyi temizle (nokta ve virgül hariç)
        cleaned = re.sub(r'[^\d,.]', '', str(price_str))
        if ',' in cleaned and '.' in cleaned:
            cleaned = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned:
            cleaned = cleaned.replace(',', '.')
        return float(cleaned)
    except:
        return 0

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200
    try:
        data = request.get_json()
        original_title = data.get("title", "")
        # ÖNEMLİ: Eklentiden gelen fiyatı alıyoruz
        original_price = clean_price(data.get("price", "0"))
        
        params = {
            "engine": "google_shopping",
            "q": original_title,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "direct_link": True
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        for item in results:
            price_raw = item.get("price", "Fiyat Yok")
            price_val = clean_price(price_raw)
            
            # --- SERT FİLTRELEME ---
            # Eğer orijinal fiyat 1.000 TL üzerindeyse ve gelen sonuç %50 daha pahalıysa LİSTEYE ALMA
            if original_price > 500:
                if price_val > (original_price * 1.5):
                    continue
            
            final_list.append({
                "site": item.get("source", "Mağaza"),
                "price": price_raw,
                "price_value": price_val,
                "image": item.get("thumbnail"),
                "link": item.get("link", ""),
                "title": item.get("title")
            })
        
        final_list.sort(key=lambda x: x['price_value'] if x['price_value'] > 0 else float('inf'))
        return jsonify({"results": final_list})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

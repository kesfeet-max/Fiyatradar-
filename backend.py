import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re

app = Flask(__name__)
CORS(app)

def clean_price(price_str):
    if not price_str: return 0
    try:
        s = str(price_str).replace('TL', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        s = re.sub(r'[^\d.]', '', s)
        return float(s)
    except: return 0

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200
    try:
        data = request.get_json()
        # Eklentiden gelen ham tarama sonuçlarını alıyoruz
        raw_results = data.get("raw_results", [])
        current_price = clean_price(data.get("price", "0"))

        final_list = []
        for item in raw_results:
            p_val = clean_price(item.get("price"))
            
            # Ticari Filtre: Aksesuar koruması ve mantıksız fiyatlar
            if current_price > 0 and (p_val < current_price * 0.5 or p_val > current_price * 1.5):
                continue
            
            final_list.append({
                "site": item.get("site"),
                "price": f"{p_val} TL",
                "price_value": p_val,
                "link": item.get("link"),
                "image": item.get("image"),
                "title": item.get("title")
            })

        final_list.sort(key=lambda x: x['price_value'])
        return jsonify({"results": final_list[:10]})

    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

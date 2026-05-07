import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re

app = Flask(__name__)
CORS(app)

# Senin RapidAPI Anahtarın
RAPIDAPI_KEY = "f64caf4ccfmsh09240838e483812p1878e8jsneb770485a2ac"
RAPIDAPI_HOST = "bluecart.p.rapidapi.com"

def clean_price(price_str):
    if not price_str: return 0
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
        current_price = clean_price(data.get("price", "0"))
        
        # Bluecart API Sorgusu
        url = "https://bluecart.p.rapidapi.com/request"
        querystring = {
            "type": "search",
            "search_term": title,
            "sort_by": "price_low_to_high"
        }
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": RAPIDAPI_HOST
        }

        response = requests.get(url, headers=headers, params=querystring)
        api_data = response.json()
        results = api_data.get("search_results", [])
        
        final_list = []
        for item in results:
            product = item.get("product", {})
            offers = item.get("offers", {}).get("primary", {})
            
            p_val = clean_price(offers.get("price", "0"))
            
            # --- PROFESYONEL FİLTRE ---
            # Ürün fiyatı baktığımızın %60'ından ucuzsa (aksesuardır) gösterme.
            if current_price > 0 and p_val < (current_price * 0.6): continue
            
            final_list.append({
                "site": offers.get("seller", "Mağaza"),
                "price": offers.get("price", "0 TL"),
                "price_value": p_val,
                "image": product.get("main_image"),
                "link": product.get("link"), # DOĞRUDAN LİNK
                "title": product.get("title")
            })
        
        return jsonify({"results": final_list[:10]})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

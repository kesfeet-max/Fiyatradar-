import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re

app = Flask(__name__)
CORS(app)

# Senin yeni profesyonel anahtarın
RAPIDAPI_KEY = "f64caf4ccfmsh09240838e483812p1878e8jsneb770485a2ac"
RAPIDAPI_HOST = "bluecart.p.rapidapi.com"

def clean_price(price_str):
    if not price_str or price_str == "0": return 0
    try:
        # Fiyatı sayıya çevirme (TL, nokta, virgül temizliği)
        s = str(price_str).replace('TL', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        s = re.sub(r'[^\d.]', '', s)
        return float(s)
    except:
        return 0

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "message": "Fiyat Radarı Pro API Aktif"}), 200

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200
    try:
        data = request.get_json()
        title = data.get("title", "")
        current_price = clean_price(data.get("price", "0"))
        
        # Bluecart API sorgusu
        url = "https://bluecart.p.rapidapi.com/request"
        querystring = {
            "type": "search",
            "search_term": title,
            "sort_by": "price_low_to_high",
            "customer_zipcode": "42000" # Konya yerel fiyatları için
        }

        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": RAPIDAPI_HOST
        }

        response = requests.get(url, headers=headers, params=querystring)
        api_data = response.json()
        
        # API'den gelen sonuçları işle
        results = api_data.get("search_results", [])
        final_list = []
        
        for item in results:
            product = item.get("product", {})
            offers = item.get("offers", {}).get("primary", {})
            
            p_raw = offers.get("price", "0")
            p_val = clean_price(p_raw)
            
            # --- PROFESYONEL FİLTRE ---
            # Eğer ürün baktığımızın yarısından ucuzsa aksesuardır, gösterme.
            if current_price > 0 and p_val < (current_price * 0.7):
                continue
            # Çok uçuk fiyatları da ele
            if current_price > 0 and p_val > (current_price * 1.4):
                continue

            final_list.append({
                "site": offers.get("seller", "Mağaza"),
                "price": f"{p_val} TL",
                "price_value": p_val,
                "image": product.get("main_image"),
                "link": product.get("link"), # Bluecart doğrudan mağaza linkini verir
                "title": product.get("title")
            })
        
        # En ucuzdan pahalıya sırala
        final_list.sort(key=lambda x: x['price_value'] if x['price_value'] > 0 else 999999)
        
        return jsonify({"results": final_list[:10]}) # En iyi 10 sonucu gönder
        
    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

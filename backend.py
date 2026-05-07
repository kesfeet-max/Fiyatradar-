import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re

app = Flask(__name__)
CORS(app)

RAPIDAPI_KEY = "f64caf4ccfmsh09240838e483812p1878e8jsneb770485a2ac"

def clean_price(price_str):
    if not price_str: return 0
    try:
        s = str(price_str).replace('TL', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        s = re.sub(r'[^\d.]', '', s)
        return float(s)
    except:
        return 0

def get_clean_title(title):
    # API'nin daha iyi sonuç bulması için gereksiz kelimeleri temizler
    ignore_words = ["fiyatı", "modelleri", "özellikleri", "gaming", "laptop", "notebook"]
    words = title.split()
    clean_words = [w for w in words if w.lower() not in ignore_words]
    return " ".join(clean_words[:4]) # Marka + Seri + Model yeterli

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200
    try:
        data = request.get_json()
        original_title = data.get("title", "")
        current_price = clean_price(data.get("price", "0"))
        
        search_query = get_clean_title(original_title)
        
        # DOĞRUDAN BLUECART OFFERS SORGUSU
        url = "https://bluecart.p.rapidapi.com/request"
        querystring = {
            "type": "search",
            "search_term": search_query,
            "sort_by": "price_low_to_high"
        }
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "bluecart.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring, timeout=5)
        api_data = response.json()
        results = api_data.get("search_results", [])
        
        final_list = []
        for item in results:
            product = item.get("product", {})
            offers = item.get("offers", {}).get("primary", {})
            
            p_val = clean_price(offers.get("price", "0"))
            source = offers.get("seller", "Mağaza").lower()
            
            # --- SERT FİLTRELEME ---
            if "letgo" in source or "dolap" in source or "sahibinden" in source:
                continue
            
            # Aksesuar veya alakasız ürün engeli (%60 - %140 aralığı)
            if current_price > 0 and (p_val < current_price * 0.6 or p_val > current_price * 1.4):
                continue
            
            # LİNK KONTROLÜ: Sadece doğrudan http ile başlayan linkleri al
            raw_link = product.get("link")
            if not raw_link or not raw_link.startswith("http"):
                continue

            final_list.append({
                "site": offers.get("seller", "Mağaza"),
                "price": f"{p_val} TL",
                "price_value": p_val,
                "image": product.get("main_image"),
                "link": raw_link, # BU LİNK DOĞRUDAN SİTEYE GİDER
                "title": product.get("title")
            })

        final_list.sort(key=lambda x: x['price_value'])
        return jsonify({"results": final_list[:8]})

    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

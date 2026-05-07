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

def shorten_title(title):
    # API'nin kafası karışmasın diye çok uzun başlıkları sadeleştiriyoruz
    words = title.split()
    return " ".join(words[:4]) 

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200
    try:
        data = request.get_json()
        original_title = data.get("title", "")
        current_price = clean_price(data.get("price", "0"))
        search_query = shorten_title(original_title)
        
        # Bluecart API
        url = "https://bluecart.p.rapidapi.com/request"
        querystring = {"type": "search", "search_term": search_query, "sort_by": "price_low_to_high"}
        headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": "bluecart.p.rapidapi.com"}

        response = requests.get(url, headers=headers, params=querystring)
        api_data = response.json()
        results = api_data.get("search_results", [])
        
        final_list = []
        for item in results:
            product = item.get("product", {})
            offers = item.get("offers", {}).get("primary", {})
            p_val = clean_price(offers.get("price", "0"))
            site_name = offers.get("seller", "").lower()

            # --- FİLTRELER ---
            # 1. Letgo ve İkinci El Engeli
            if "letgo" in site_name or "dolap" in site_name or "sahibinden" in site_name:
                continue
            
            # 2. Çok ucuz (aksesuar) veya çok pahalı filtrelemesi
            if current_price > 0 and (p_val < current_price * 0.7 or p_val > current_price * 1.3):
                continue
            
            final_list.append({
                "site": offers.get("seller", "Mağaza"),
                "price": f"{p_val} TL",
                "price_value": p_val,
                "image": product.get("main_image"),
                "link": product.get("link"), # Bluecart linki
                "title": product.get("title")
            })

        # Eğer Bluecart sonuç vermezse B Planı (SerpApi) ama orada da Letgo'yu eliyoruz
        if not final_list:
            params = {
                "engine": "google_shopping",
                "q": search_query,
                "api_key": "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201",
                "hl": "tr", "gl": "tr", "direct_link": True
            }
            res = requests.get("https://serpapi.com/search.json", params=params)
            google_results = res.json().get("shopping_results", [])
            
            for item in google_results:
                p_val = clean_price(item.get("price", "0"))
                source = item.get("source", "").lower()
                
                if "letgo" in source or "dolap" in source: continue
                if current_price > 0 and (p_val < current_price * 0.7 or p_val > current_price * 1.3): continue
                
                final_list.append({
                    "site": item.get("source", "Mağaza"),
                    "price": item.get("price"),
                    "price_value": p_val,
                    "image": item.get("thumbnail"),
                    "link": item.get("link"), # Google Shopping doğrudan linki
                    "title": item.get("title")
                })

        final_list.sort(key=lambda x: x['price_value'] if x['price_value'] > 0 else 999999)
        return jsonify({"results": final_list[:10]})

    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

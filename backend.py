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
        # Fiyatı sayıya çevirme işlemi
        s = str(price_str).replace('TL', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        s = re.sub(r'[^\d.]', '', s)
        return float(s)
    except:
        return 0

def get_smart_title(title):
    # Başlığı temizle: API'nin kafasını karıştıran çok uzun metinleri at
    words = title.split()
    # İlk 4 kelime genelde Marka + Modeldir (Örn: Casper Excalibur G870)
    return " ".join(words[:4])

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200
    try:
        data = request.get_json()
        original_title = data.get("title", "")
        current_price = clean_price(data.get("price", "0"))
        
        search_query = get_smart_title(original_title)
        
        url = "https://bluecart.p.rapidapi.com/request"
        
        # KRİTİK AYAR: Türkiye sonuçları için "google_domain" ve "gl" ekledik
        querystring = {
            "type": "search",
            "search_term": search_query,
            "google_domain": "google.com.tr",
            "gl": "tr", 
            "hl": "tr",
            "sort_by": "price_low_to_high"
        }
        
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "bluecart.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        api_data = response.json()
        
        results = api_data.get("search_results", [])
        final_list = []
        
        for item in results:
            product = item.get("product", {})
            offers = item.get("offers", {}).get("primary", {})
            
            p_val = clean_price(offers.get("price", "0"))
            source = offers.get("seller", "Mağaza").lower()
            
            # İkinci el ve alakasız siteleri engelle
            if any(x in source for x in ["letgo", "dolap", "sahibinden", "gardrops"]):
                continue

            # Fiyat Filtresi: Baktığın ürünün %50'sinden ucuzsa aksesuardır, gösterme
            if current_price > 0 and p_val < (current_price * 0.5):
                continue

            link = product.get("link")
            if link and link.startswith("http"):
                final_list.append({
                    "site": offers.get("seller", "Mağaza"),
                    "price": f"{p_val} TL",
                    "price_value": p_val,
                    "image": product.get("main_image"),
                    "link": link,
                    "title": product.get("title")
                })

        # Eğer hala sonuç yoksa (Bluecart TR'de zayıf kalırsa) manuel bir arama linki oluştur
        if not final_list:
             final_list.append({
                "site": "Google Shopping",
                "price": "Sonuçları Gör",
                "price_value": 0,
                "image": "https://www.google.com/favicon.ico",
                "link": f"https://www.google.com/search?q={search_query}&tbm=shop",
                "title": "Diğer mağazalara göz at"
            })

        return jsonify({"results": final_list})

    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

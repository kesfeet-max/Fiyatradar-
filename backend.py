import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re

app = Flask(__name__)
CORS(app)

# Bu anahtar sadece destekleyici veri için kullanılacak
RAPIDAPI_KEY = "f64caf4ccfmsh09240838e483812p1878e8jsneb770485a2ac"

def clean_price(price_str):
    if not price_str: return 0
    try:
        s = str(price_str).replace('TL', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        s = re.sub(r'[^\d.]', '', s)
        return float(s)
    except: return 0

def extract_model(title):
    # Ürünün kimliğini belirleyen en önemli 3-4 kelimeyi ayıklar
    # Örn: "Casper Excalibur G870.1245-BV60X-B" -> "Casper Excalibur G870"
    words = title.split()
    return " ".join(words[:4])

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200
    try:
        data = request.get_json()
        full_title = data.get("title", "")
        current_price = clean_price(data.get("price", "0"))
        
        target_model = extract_model(full_title)
        
        # PRO SİSTEM: Bluecart üzerinden 'ÖZEL TEKLİFLER' (Offers) sorgusu
        # Bu sorgu doğrudan Trendyol/Hepsiburada gibi yerlerin verisini getirir
        url = "https://bluecart.p.rapidapi.com/request"
        querystring = {
            "type": "search",
            "search_term": target_model,
            "google_domain": "google.com.tr",
            "gl": "tr",
            "hl": "tr",
            "sort_by": "price_low_to_high"
        }
        
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "bluecart.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring, timeout=12)
        api_data = response.json()
        
        results = api_data.get("search_results", [])
        final_results = []
        
        for item in results:
            prod = item.get("product", {})
            offer = item.get("offers", {}).get("primary", {})
            
            price_val = clean_price(offer.get("price", "0"))
            seller = offer.get("seller", "Mağaza")
            
            # --- TİCARİ FİLTRELEME (Cimri Standartı) ---
            # 1. İkinci el sitelerini tamamen yasakla (Gelir elde edemezsin)
            if any(x in seller.lower() for x in ["letgo", "dolap", "sahibinden", "gardrops"]):
                continue
            
            # 2. Ürün doğruluğu kontrolü: Fiyat baktığımızdan çok düşükse o parçadır/aksesuardır
            if current_price > 0 and price_val < (current_price * 0.5):
                continue

            link = prod.get("link")
            if link and link.startswith("http"):
                final_results.append({
                    "site": seller,
                    "price": f"{price_val} TL",
                    "price_value": price_val,
                    "image": prod.get("main_image"),
                    "link": link, # Bu link üzerinden ileride Affiliate geliri tanımlayacağız
                    "title": prod.get("title")
                })

        # En ucuzu başa al
        final_results.sort(key=lambda x: x['price_value'])
        
        return jsonify({"results": final_results[:10]})

    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

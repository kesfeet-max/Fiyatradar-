import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re

app = Flask(__name__)
CORS(app)

# Profesyonel API Anahtarı (Sadece yedek olarak duracak)
RAPIDAPI_KEY = "f64caf4ccfmsh09240838e483812p1878e8jsneb770485a2ac"

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
        title = data.get("title", "")
        current_price = clean_price(data.get("price", "0"))
        
        # 1. ADIM: Ürün ismini 'saf' hale getir (Marka + Model)
        # Karmaşık teknik detayları temizle ki her sitede ortak bulunsun
        clean_title = " ".join(title.split()[:4]) 
        
        # 2. ADIM: "Cimri Modu" - Çoklu Kaynak Taraması
        # Sadece bir yere bakmıyoruz, RapidAPI üzerinden 'shopping' motorunu en geniş haliyle zorluyoruz
        url = "https://bluecart.p.rapidapi.com/request"
        querystring = {
            "type": "search",
            "search_term": clean_title,
            "google_domain": "google.com.tr",
            "gl": "tr",
            "hl": "tr",
            "sort_by": "price_low_to_high"
        }
        
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "bluecart.p.rapidapi.com"
        }

        # Veriyi çek
        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        api_data = response.json()
        
        results = api_data.get("search_results", [])
        final_list = []
        
        for item in results:
            prod = item.get("product", {})
            offer = item.get("offers", {}).get("primary", {})
            
            p_val = clean_price(offer.get("price", "0"))
            store = offer.get("seller", "Mağaza")
            
            # --- TİCARİ SÜZGEÇ ---
            # İkinci el sitelerini (Letgo vb.) ve geçersiz fiyatları Cimri gibi eliyoruz
            if any(x in store.lower() for x in ["letgo", "dolap", "sahibinden", "gardrops"]): continue
            if current_price > 0 and (p_val < current_price * 0.6): continue # Aksesuar engeli

            # Linki ve veriyi paketle
            final_list.append({
                "site": store,
                "price": f"{p_val} TL",
                "price_value": p_val,
                "image": prod.get("main_image"),
                "link": prod.get("link"), # DOĞRUDAN MAĞAZA LİNKİ
                "title": prod.get("title")
            })

        # Fiyatları sırala (Cimri'nin en sevdiği iş)
        final_list.sort(key=lambda x: x['price_value'])
        
        return jsonify({"results": final_list[:10]})

    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

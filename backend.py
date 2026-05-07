import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re

app = Flask(__name__)
CORS(app)

# TİCARİ GELİR KODUN (Buraya ileride Trendyol Partner ID'ni koyacaksın)
MY_AFFILIATE_ID = "mevlut_kocak_42"

def clean_price(price_str):
    if not price_str: return 0
    try:
        s = str(price_str).replace('TL', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        s = re.sub(r'[^\d.]', '', s)
        return float(s)
    except: return 0

def get_trendyol_direct(query):
    """Trendyol'un API'sini taklit ederek doğrudan ürün ve link getirir."""
    try:
        # Trendyol arama motoruna doğrudan istek atıyoruz
        search_url = f"https://public.trendyol.com/discovery-web-search-service/v1/explore?q={query.replace(' ', '%20')}&pi=0&os=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json"
        }
        res = requests.get(search_url, headers=headers, timeout=10)
        data = res.json()
        
        products = data.get('productSearchResult', {}).get('products', [])
        if products:
            item = products[0] # En üstteki (genelde en alakalı) ürün
            p_name = item.get('name')
            p_price = item.get('price', {}).get('sellingPrice')
            p_url = "https://www.trendyol.com" + item.get('url')
            p_img = "https://cdn.dsmcdn.com" + item.get('images')[0]
            
            # PARA KAZANDIRAN DOKUNUŞ: Linke senin kodunu ekliyoruz
            affiliate_link = f"{p_url}?boutiqueId=61&merchantId={item.get('merchantId')}&sav={MY_AFFILIATE_ID}"
            
            return {
                "site": "Trendyol",
                "price": f"{p_price} TL",
                "price_value": p_val if (p_val := clean_price(p_price)) else 0,
                "link": affiliate_link,
                "image": p_img,
                "title": p_name
            }
    except: return None

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200
    try:
        data = request.get_json()
        title = data.get("title", "")
        current_price = clean_price(data.get("price", "0"))
        
        # Marka + Model
        search_query = " ".join(title.split()[:4])
        
        final_list = []
        
        # 1. Kendi Botumuz (Trendyol)
        ty = get_trendyol_direct(search_query)
        if ty: final_list.append(ty)
        
        # 2. Buraya Hepsiburada ve Amazon botlarını da ekleyeceğiz...

        if not final_list:
            return jsonify({"results": [], "message": "Pazar yerlerinden veri alınamadı."})

        return jsonify({"results": final_list})

    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

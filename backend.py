import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re

app = Flask(__name__)
CORS(app)

# Senin profesyonel RapidAPI anahtarın (Bluecart için)
RAPIDAPI_KEY = "f64caf4ccfmsh09240838e483812p1878e8jsneb770485a2ac"

def clean_price(price_str):
    if not price_str: return 0
    try:
        s = str(price_str).replace('TL', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        s = re.sub(r'[^\d.]', '', s)
        return float(s)
    except: return 0

def get_pure_model(title):
    # Ürün isminden sadece marka ve ana modeli çeker (Örn: Casper Excalibur G870)
    # Satıcıların eklediği "Gaming", "Laptop" gibi çöpleri temizler
    ignore = ["gaming", "laptop", "notebook", "fiyatı", "ve", "özellikleri", "siyah", "gri"]
    words = title.split()
    clean = [w for w in words if w.lower() not in ignore]
    return " ".join(clean[:3]) # Sadece en kritik 3 kelime

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200
    try:
        data = request.get_json()
        title = data.get("title", "")
        current_price = clean_price(data.get("price", "0"))
        
        # 1. ADIM: Arama terimini pürüzsüzleştir
        model_name = get_pure_model(title)
        
        # 2. ADIM: Bluecart üzerinden "DOĞRUDAN MAĞAZA" tekliflerini çek
        url = "https://bluecart.p.rapidapi.com/request"
        querystring = {
            "type": "search",
            "search_term": model_name,
            "sort_by": "price_low_to_high",
            "customer_zipcode": "42000" # Konya/Türkiye lokasyonu
        }
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "bluecart.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring, timeout=12)
        api_results = response.json().get("search_results", [])
        
        final_list = []
        for item in api_results:
            prod = item.get("product", {})
            off = item.get("offers", {}).get("primary", {})
            
            p_val = clean_price(off.get("price", "0"))
            store = off.get("seller", "Mağaza")
            
            # --- CİMRİ TARZI FİLTRELEME ---
            # İkinci el engeli
            if any(x in store.lower() for x in ["letgo", "dolap", "sahibinden"]): continue
            # Aksesuar engeli (Baktığın ürünün %60'ından ucuzsa o parça veya kılıftır)
            if current_price > 0 and p_val < (current_price * 0.6): continue
            # Stokta olmayan veya linki bozuk olanları ele
            link = prod.get("link")
            if not link or not link.startswith("http"): continue

            final_list.append({
                "site": store,
                "price": f"{p_val} TL",
                "price_value": p_val,
                "image": prod.get("main_image"),
                "link": link, # Bu link doğrudan mağazaya uçurur
                "title": prod.get("title")
            })

        # Fiyata göre diz
        final_list.sort(key=lambda x: x['price_value'])
        
        return jsonify({"results": final_list[:10]})

    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

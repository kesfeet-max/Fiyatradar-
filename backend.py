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
        title = data.get("title", "")
        current_price = clean_price(data.get("price", "0"))
        
        # BİZİM ÖZEL ALGORİTMAMIZ: 
        # Marka ve model ismini ayıklayıp doğrudan pazar yerlerine "ateş" edeceğiz
        search_query = " ".join(title.split()[:4])
        
        # İleride buraya 'TrendyolScraper', 'HepsiburadaScraper' gibi kendi fonksiyonlarımızı ekleyeceğiz.
        # Şimdilik en hızlı sonuç için SerpApi'yi 'Direct Link' modunda en profesyonel haliyle kullanıyoruz.
        
        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201",
            "hl": "tr", "gl": "tr",
            "direct_link": True # Google'ı pas geç, doğrudan mağazayı getir
        }

        response = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        for item in results:
            p_val = clean_price(item.get("price", "0"))
            source = item.get("source", "").lower()
            
            # Letgo vb. çöpleri temizle
            if any(x in source for x in ["letgo", "dolap", "sahibinden"]): continue
            
            # Baktığımız ürünle fiyat uyumunu kontrol et (Aksesuar koruması)
            if current_price > 0 and (p_val < current_price * 0.6 or p_val > current_price * 1.5): continue

            final_list.append({
                "site": item.get("source", "Mağaza"),
                "price": f"{p_val} TL",
                "price_value": p_val,
                "image": item.get("thumbnail"),
                "link": item.get("link"), # direct_link sayesinde ARTIK GOOGLE'A ATMAZ
                "title": item.get("title")
            })

        final_list.sort(key=lambda x: x['price_value'])
        
        return jsonify({"results": final_list[:10]})

    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

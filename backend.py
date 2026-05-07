import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_price(price_str):
    """Her türlü fiyat formatını (15.000,00 TL veya 185000) sayıya çevirir."""
    if not price_str: return 0
    try:
        # Sadece sayıları ve son virgül/noktayı tutmaya çalış
        s = str(price_str).replace('TL', '').replace(' ', '').strip()
        # Binlik ayırıcı noktaları sil, virgülü noktaya çevir
        if ',' in s and '.' in s:
            s = s.replace('.', '').replace(',', '.')
        elif ',' in s:
            s = s.replace(',', '.')
        
        # Sayı olmayan karakterleri tamamen temizle
        s = re.sub(r'[^\d.]', '', s)
        return float(s)
    except:
        return 0

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200
    try:
        data = request.get_json()
        original_title = data.get("title", "")
        # Trendyol'dan gelen fiyat
        original_price = clean_price(data.get("price", "0"))
        
        params = {
            "engine": "google_shopping",
            "q": original_title,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "direct_link": True
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        for item in results:
            price_raw = item.get("price", "0")
            price_val = clean_price(price_raw)
            
            # --- ANA FİLTRE ---
            # Eğer orijinal fiyatımız varsa ve gelen sonuç bu fiyatın 1.4 katından (yüzde 40 fazlasından) 
            # daha pahalıysa, o ürünü listeye ASLA ALMA.
            if original_price > 0:
                if price_val > (original_price * 1.4):
                    continue # Bu ürünü atla
            
            final_list.append({
                "site": item.get("source", "Mağaza"),
                "price": price_raw,
                "price_value": price_val,
                "image": item.get("thumbnail"),
                "link": item.get("link", ""),
                "title": item.get("title")
            })
        
        final_list.sort(key=lambda x: x['price_value'] if x['price_value'] > 0 else float('inf'))
        return jsonify({"results": final_list})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

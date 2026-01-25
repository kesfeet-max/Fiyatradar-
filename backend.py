import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def parse_price(price_str):
    if not price_str: return 0
    try:
        val = re.sub(r'[^\d]', '', str(price_str).split(',')[0])
        return int(val)
    except: return 0

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        original_title = data.get("title", "").lower()
        current_price = parse_price(data.get("price", "0"))
        
        is_set = any(word in original_title for word in ["set", "takım", "3'lü", "komple"])
        
        # Apple ve Saat gibi varyasyonlu ürünler için kapasite/model kilidi
        must_contain = re.findall(r'(\d+\s*[gt]b|pro\s*max|ultra)', original_title)

        search_words = original_title.split()[:5]
        search_query = " ".join(search_words)

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "num": "40"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        forbidden = ["tel", "izgara", "yedek", "parça", "aksesuar", "filtre", "kitap", "dvd", "ikinci el", "kordon", "kılıf"]

        for item in results:
            item_title = item.get("title", "").lower()
            item_price = parse_price(item.get("price"))
            
            # --- LİNK DÜZELTME (Boş sayfa açılmasını engelleyen kısım) ---
            # link yoksa product_link, o da yoksa serpapi_link dene
            valid_link = item.get("link") or item.get("product_link") or item.get("serpapi_product_api")

            # --- AKILLI FİLTRELER ---

            # 1. Boş linkleri ele
            if not valid_link:
                continue

            # 2. GB/TB ve Model Kilidi (iPhone hatasını çözer)
            if must_contain and not all(spec in item_title for spec in must_contain):
                continue

            # 3. Set Kontrolü
            if is_set and not any(word in item_title for word in ["set", "takım", "3'lü"]):
                continue

            # 4. Fiyat Sapması (134k saate 14k göstermez)
            if current_price > 1000:
                # Fiyat farkı %50'den fazlaysa şüphelidir, gösterme
                if item_price < (current_price * 0.50) or item_price > (current_price * 2.0):
                    continue

            # 5. Yasaklı Kelime Kontrolü
            if any(f in item_title for f in forbidden) and not any(f in original_title for f in forbidden):
                continue

            final_list.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": valid_link,
                "image": item.get("thumbnail"),
                "raw_price": item_price
            })
        
        final_list.sort(key=lambda x: x['raw_price'])
        
        # Eğer hiç sonuç kalmadıysa (filtreler hepsini elediyse) 
        # Kullanıcıya dürüstçe boş liste döndür
        return jsonify({"results": final_list[:8]})
        
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

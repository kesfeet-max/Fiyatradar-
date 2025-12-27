import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_price(price_str):
    try:
        # Fiyatı sayıya çevirir
        cleaned = re.sub(r'[^\d,]', '', str(price_str)).replace(',', '.')
        return float(cleaned)
    except:
        return 0.0

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return "", 200
    
    data = request.get_json(silent=True) or {}
    title = data.get("title", "")
    orig_price_str = data.get("original_price", "0")
    base_price = clean_price(orig_price_str)

    search_query = ' '.join(title.split()[:5])
    
    params = {
        "engine": "google_shopping",
        "q": search_query,
        "hl": "tr",
        "gl": "tr", # Sadece Türkiye sonuçlarını zorla
        "api_key": SERP_API_KEY
    }

    try:
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=15)
        shopping_results = response.json().get("shopping_results", [])
        
        # Site bazlı en ucuzları tutmak için sözlük
        best_prices = {}
        
        forbidden_keywords = ["yedek", "parça", "filtre", "deterjan", "hortum", "aparat", "başlık", "aksesuar"]
        # Yabancı siteleri engellemek için liste
        forbidden_sites = ["microless", "al jedayel", "desertcart", "ubuy", "amazon.com", "ebay", "aliexpress"]

        for item in shopping_results:
            site_name = item.get("source", "Bilinmeyen Satıcı")
            site_key = site_name.lower()
            actual_link = item.get("link") or item.get("product_link")
            
            if not actual_link: continue

            # FİLTRE 1: Yabancı site engelleme
            if any(forbidden in site_key for forbidden in forbidden_sites) or site_key.endswith(".com"):
                if "com.tr" not in site_key: # .com.tr ise izin ver
                    continue

            item_price = clean_price(item.get("price", "0"))
            item_title = item.get("title", "").lower()
            
            # FİLTRE 2: Aksesuar ve Fiyat Sapma Kontrolü
            is_accessory = any(word in item_title for word in forbidden_keywords)
            is_too_cheap = item_price < (base_price * 0.4) if base_price > 0 else False
            
            if not is_accessory and not is_too_cheap:
                # FİLTRE 3: Site başına sadece en ucuzu seç
                if site_key not in best_prices or item_price < best_prices[site_key]['price_num']:
                    best_prices[site_key] = {
                        "title": item.get("title", ""),
                        "site": site_name,
                        "price": item.get("price", "Fiyat Yok"),
                        "price_num": item_price,
                        "link": actual_link 
                    }

        # Sözlüğü listeye çevir ve fiyata göre sırala
        final_results = sorted(best_prices.values(), key=lambda x: x['price_num'])
        
        # 'price_num' bilgisini temizleyip gönder
        output = []
        for res in final_results[:10]:
            del res['price_num']
            output.append(res)

        return jsonify({"results": output}) 
    except:
        return jsonify({"results": []}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

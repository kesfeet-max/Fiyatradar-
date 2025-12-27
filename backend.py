import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_price(price_str):
    try:
        # Fiyatı sayıya çevirir: '51.343,06 TL' -> 51343.06
        cleaned = re.sub(r'[^\d,]', '', str(price_str)).replace(',', '.')
        return float(cleaned)
    except:
        return 0.0

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return "", 200
    
    data = request.get_json(silent=True) or {}
    full_title = data.get("title", "")
    orig_price_str = data.get("original_price", "0")
    base_price = clean_price(orig_price_str)

    # 1. Deneme: Tam başlık | 2. Deneme: İlk 6 kelime (Marka/Model odağı)
    search_queries = [full_title, " ".join(full_title.split()[:6])]
    
    shopping_results = []
    for q in search_queries:
        if not q: continue
        params = {"engine": "google_shopping", "q": q, "hl": "tr", "gl": "tr", "api_key": SERP_API_KEY}
        try:
            r = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
            res = r.json().get("shopping_results", [])
            if res:
                shopping_results = res
                break
        except: continue

    best_prices = {}
    # Yasaklı yabancı siteler
    blacklist = ["microless", "al jedayel", "desertcart", "ubuy", "speedcomputers", "ebay", "aliexpress", "u-buy"]

    for item in shopping_results:
        site_name = item.get("source", "").lower()
        link = item.get("link") or item.get("product_link")
        price = clean_price(item.get("price", "0"))
        
        if not link or price == 0: continue
        if any(bad in site_name for bad in blacklist): continue

        # Sadece TR siteleri (Domain veya büyük pazaryerleri)
        is_tr = any(ext in link.lower() for ext in [".tr", "n11.com", "trendyol.com", "hepsiburada.com", "vatanbilgisayar", "teknosa", "pazarama", "ciceksepeti"])
        if not is_tr: continue

        # FİLTRE: Eğer aranan ürün bulunamıyorsa eşiği biraz yükseltiyoruz (+200 TL hata payı)
        # Bu sayede manuel gördüğün tüm ucuz seçenekler listeye girer
        if base_price > 0 and price > (base_price + 200): continue

        if site_name not in best_prices or price < best_prices[site_name]['price_num']:
            best_prices[site_name] = {
                "title": item.get("title", ""),
                "site": item.get("source", "Satıcı"),
                "price": item.get("price", "Fiyat Yok"),
                "price_num": price,
                "link": link 
            }

    results = sorted(best_prices.values(), key=lambda x: x['price_num'])
    for r in results: del r['price_num']

    return jsonify({"results": results})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

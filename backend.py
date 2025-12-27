import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_price(price_str):
    try:
        # Fiyat metninden sadece sayıları ve kuruşu ayıklar
        cleaned = re.sub(r'[^\d,]', '', str(price_str)).replace(',', '.')
        return float(cleaned)
    except:
        return 0.0

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return "", 200
    
    data = request.get_json(silent=True) or {}
    # Başlığın tamamını alıyoruz (Kısıtlama kaldırıldı)
    title = data.get("title", "")
    orig_price_str = data.get("original_price", "0")
    base_price = clean_price(orig_price_str)

    # SERP API parametreleri: hl=tr ve gl=tr Türkiye sonuçlarını zorlar
    params = {
        "engine": "google_shopping",
        "q": title, 
        "hl": "tr",
        "gl": "tr",
        "api_key": SERP_API_KEY
    }

    try:
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=15)
        shopping_results = response.json().get("shopping_results", [])
        
        best_prices = {}
        # Yabancı siteleri engellemek için kara liste
        blacklist = ["microless", "al jedayel", "desertcart", "ubuy", "speedcomputers", "ebay", "aliexpress", "u-buy"]

        for item in shopping_results:
            site_name = item.get("source", "").lower()
            actual_link = item.get("link") or item.get("product_link")
            item_price = clean_price(item.get("price", "0"))
            
            if not actual_link or item_price == 0: continue

            # FİLTRE 1: Yabancı site engelleme
            if any(bad in site_name for bad in blacklist):
                continue

            # FİLTRE 2: Sadece Türkiye siteleri (.tr uzantısı veya büyük yerli pazaryerleri)
            is_tr = any(ext in actual_link.lower() for ext in [".tr", "n11.com", "trendyol.com", "hepsiburada.com", "ciceksepeti.com"])
            if not is_tr:
                continue

            # FİLTRE 3: Sadece DAHA UCUZ olanları getir
            # 10.000 TL'lik üründe 9.995 TL ve altını kabul eder
            if base_price > 0 and item_price >= (base_price - 1):
                continue

            # Her siteden sadece en düşük fiyatı seç
            if site_name not in best_prices or item_price < best_prices[site_name]['price_num']:
                best_prices[site_name] = {
                    "title": item.get("title", ""),
                    "site": item.get("source", "Satıcı"),
                    "price": item.get("price", "Fiyat Yok"),
                    "price_num": item_price,
                    "link": actual_link 
                }

        # En ucuzdan başlayarak sırala
        final_results = sorted(best_prices.values(), key=lambda x: x['price_num'])
        
        output = []
        for res in final_results:
            del res['price_num']
            output.append(res)

        return jsonify({"results": output}) 
    except:
        return jsonify({"results": []}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_price(price_str):
    try:
        # Fiyatı sayıya dönüştürür (51.343,06 -> 51343.06)
        cleaned = re.sub(r'[^\d,]', '', str(price_str)).replace(',', '.')
        return float(cleaned)
    except:
        return 0.0

@app.route("/compare", methods=["POST"])
def compare():
    data = request.get_json()
    full_title = data.get("title", "")
    orig_price = clean_price(data.get("original_price", "0"))

    # ZEKİ ARAMA: Eğer tam başlık sonuç vermezse diye kısa versiyonu da hazırlıyoruz
    search_query = " ".join(full_title.split()[:5]) 

    params = {
        "engine": "google_shopping",
        "q": search_query,
        "hl": "tr",
        "gl": "tr", # Sadece Türkiye sonuçları
        "api_key": SERP_API_KEY
    }

    try:
        response = requests.get("https://serpapi.com/search.json", params=params)
        shopping_results = response.json().get("shopping_results", [])
    except:
        return jsonify({"results": []})

    best_prices = {}
    # Güvenli Türkiye mağazaları ve genel pazaryerleri
    whitelist = ["trendyol", "hepsiburada", "n11", "amazon.com.tr", "vatan", "teknosa", "pazarama", "koctas", "ciceksepeti"]

    for item in shopping_results:
        site = item.get("source", "").lower()
        price = clean_price(item.get("price", "0"))
        link = item.get("link")

        if not link or price == 0: continue
        
        # Sadece bilinen TR siteleri veya TR uzantılı linkler
        is_tr_site = any(w in site for w in whitelist) or ".tr" in link.lower()
        
        if is_tr_site:
            if site not in best_prices or price < best_prices[site]['price_num']:
                best_prices[site] = {
                    "site": item.get("source"),
                    "price": item.get("price"),
                    "link": link,
                    "price_num": price
                }

    # Sonuçları fiyata göre sırala ve listeye çevir
    final_list = sorted(best_prices.values(), key=lambda x: x['price_num'])
    for item in final_list: del item['price_num']

    return jsonify({"results": final_list})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

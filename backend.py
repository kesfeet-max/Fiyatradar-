import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_price(price_str):
    if not price_str: return 0
    try:
        # Fiyatı sayıya çevir (Örn: "16.699 TL" -> 16699.0)
        cleaned = re.sub(r'[^\d]', '', str(price_str))
        return float(cleaned)
    except: return 0

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        full_title = data.get("title", "")
        
        # Arama terimine "cep telefonu" ekleyerek aksesuar çıkma ihtimalini azaltıyoruz
        search_query = " ".join(full_title.split()[:4]) + " cep telefonu"

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr"
        }

        response = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        results = response.json().get("shopping_results", [])
        
        # Orijinal ürünün yaklaşık fiyatını belirle (Hepsiburada/Trendyol fiyatı gibi)
        # Eğer fiyat çekilemiyorsa çok düşük fiyatları filtrelemek için 5000 TL alt sınır koyuyoruz
        min_allowed_price = 5000 

        final_results = []
        whitelist = ["trendyol", "hepsiburada", "n11", "amazon", "vatan", "teknosa", "pazarama"]

        for item in results:
            price_val = clean_price(item.get("price"))
            source = item.get("source", "").lower()
            title = item.get("title", "").lower()
            
            # FİLTRELEME MANTIĞI:
            # 1. Fiyat 5000 TL'den düşükse (yedek parça/kılıf olma ihtimali yüksek) alma.
            # 2. Başlıkta "kılıf", "cam", "cover", "aksesuar" geçiyorsa alma.
            illegal_words = ["kılıf", "cam", "kapak", "cover", "lens", "film", "yedek", "parça"]
            is_accessory = any(word in title for word in illegal_words)

            if price_val > min_allowed_price and not is_accessory:
                if any(w in source for w in whitelist):
                    final_results.append({
                        "site": item.get("source"),
                        "price": item.get("price"),
                        "link": item.get("link") or item.get("product_link")
                    })
        
        # Fiyata göre artan sırala (En ucuz gerçek telefon en üstte)
        final_results.sort(key=lambda x: clean_price(x['price']))

        return jsonify({"results": final_results[:6]})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    app.run()

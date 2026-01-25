import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os
import statistics

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
        
        # 1. STRATEJİ: Sorguyu tırnak içinde göndererek 'KESİN' sonuç iste
        # "Samsung Galaxy Tab A11"
        brand_model_parts = original_title.split()[:4]
        refined_query = " ".join(brand_model_parts)

        params = {
            "engine": "google_shopping",
            "q": f'"{refined_query}"', 
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "num": "50"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        if not results:
            return jsonify({"results": []})

        # 2. ADIM: Fiyat Kümeleme (Outlier Detection)
        # Gelen tüm fiyatların bir listesini çıkar
        prices = [parse_price(item.get("price")) for item in results if parse_price(item.get("price")) > 0]
        
        if len(prices) > 5:
            median_price = statistics.median(prices)
        else:
            median_price = current_price

        final_list = []
        # En tehlikeli kelimeler (Ürün değilse elediklerimiz)
        bad_words = ["kitap", "kılıf", "ekran koruyucu", "yedek parça", "aparat", "aksesuar", "ikinci el", "tamir"]

        for item in results:
            item_title = item.get("title", "").lower()
            item_price = parse_price(item.get("price"))
            actual_link = item.get("link") or item.get("product_link")

            if not actual_link or item_price == 0: continue

            # --- CIMRI MANTIĞI: DOĞRULAMA ---

            # A) FİYAT TESTİ: Ortalamanın veya bakılan fiyatın %40'ından daha ucuzsa ELE.
            # (8000 TL'lik tablet için 3200 TL altı her şey elenir -> Kitaplar gider)
            if item_price < (current_price * 0.40) or item_price < (median_price * 0.40):
                continue

            # B) KELİME TESTİ: Marka ve Model anahtar kelimeleri mutlaka geçmeli
            # (Samsung ve Tab kelimeleri yoksa o ürünü gösterme)
            if not all(word in item_title for word in brand_model_parts[:2]):
                continue

            # C) YASAKLI KELİME: Orijinal başlıkta yoksa sonuçta da olmasın
            if any(bw in item_title for bw in bad_words) and not any(bw in original_title for bw in bad_words):
                continue

            final_list.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": actual_link,
                "image": item.get("thumbnail"),
                "raw_price": item_price
            })
        
        # Fiyat sıralaması
        final_list.sort(key=lambda x: x['raw_price'])
        
        return jsonify({"results": final_list[:10]})
        
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

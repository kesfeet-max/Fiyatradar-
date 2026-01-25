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
        original_title = data.get("title", "")
        current_price = parse_price(data.get("price", "0"))
        
        # 1. ARAMA STRATEJİSİ: Daha fazla sonuç çekelim (40 -> 60)
        # Sadece Marka + Model alarak n11/Hepsiburada'daki tüm varyasyonları yakala
        clean_title = " ".join(original_title.split()[:6])
        
        params = {
            "engine": "google_shopping",
            "q": clean_title,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "num": "60" 
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        forbidden = ["yedek parça", "aparat", "aksesuar", "kordon", "kılıf", "ikinci el"]

        for item in results:
            item_title = item.get("title", "")
            item_price = parse_price(item.get("price"))
            actual_link = item.get("link") or item.get("product_link")

            if not actual_link or item_price == 0: continue

            # 2. AKILLI EŞİK (200 TL HATASINI ÇÖZEN KISIM)
            # Eğer fiyat farkı %15'ten az ise (Örn: 8000 TL vs 7800 TL) HİÇ SORGULAMA, GÖSTER.
            # Çünkü bu gerçek bir rekabet fiyatıdır.
            diff_ratio = abs(item_price - current_price) / current_price if current_price > 0 else 0
            
            is_valid = False
            if diff_ratio < 0.15: 
                is_valid = True # Küçük farklar her zaman geçerli
            elif diff_ratio < 0.45:
                # Orta farklarda (Örn: 8000 TL vs 5000 TL) kelime kontrolü yap
                match_count = sum(1 for word in clean_title.split() if word.lower() in item_title.lower())
                if match_count >= 2:
                    is_valid = True
            
            # 3. YASAKLI KELİME (Sadece bariz hataları ele)
            if any(f in item_title.lower() for f in forbidden) and not any(f in original_title.lower() for f in forbidden):
                is_valid = False

            if is_valid:
                final_list.append({
                    "site": item.get("source"),
                    "price": item.get("price"),
                    "link": actual_link,
                    "image": item.get("thumbnail"),
                    "raw_price": item_price
                })
        
        # 4. AYNI SİTEYİ TEKRAR GÖSTERME (Trendyol'dayken Trendyol'u gösterme)
        current_url = data.get("url", "")
        filtered_list = [i for i in final_list if i['site'].lower() not in current_url.lower()]

        # Fiyata göre sırala
        filtered_list.sort(key=lambda x: x['raw_price'])
        
        return jsonify({"results": filtered_list[:10]})
        
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

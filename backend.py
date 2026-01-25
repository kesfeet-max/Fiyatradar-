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
        # Kullanıcının baktığı ürünün fiyatı (En büyük silahımız!)
        current_page_price = parse_price(data.get("price", "0"))
        
        # Arama sorgusunu optimize et
        search_query = " ".join(original_title.split()[:5])

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr",
            "num": "40"
        }

        response = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        # KRİTİK: Yedek parça ve alakasız ürünleri eleyen sözlük
        forbidden = ["tel", "izgara", "yedek", "parça", "aksesuar", "kılıf", "cam", "dvd", "ikinci el", "2.el", "kapak", "hazne"]

        for item in results:
            item_title = item.get("title", "").lower()
            item_price = parse_price(item.get("price"))
            
            # --- ZEKA KONTROLÜ 1: FİYAT BANDI ---
            # Eğer bulunan ürün, orijinalinden %40'tan fazla ucuzsa %99 yedek parçadır.
            # Örn: 1500 TL'lik Airfryer ararken 800 TL'lik tel gelirse elenir.
            if current_page_price > 0:
                if item_price < (current_page_price * 0.65): 
                    continue

            # --- ZEKA KONTROLÜ 2: KELİME ANALİZİ ---
            # Başlıkta "tel", "izgara" gibi yedek parça kelimeleri geçiyor mu?
            if any(word in item_title for word in forbidden):
                # Eğer orijinal ürünün başlığında bu yasaklı kelime YOKSA ama sonuçta VARSA ele.
                if not any(word in original_title for word in forbidden):
                    continue

            # --- ZEKA KONTROLÜ 3: MARKA EŞLEŞMESİ ---
            # Markanın (örn: Kumtel) başlıkta geçtiğinden emin ol.
            brand = original_title.split()[0]
            if brand not in item_title:
                continue

            final_list.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": item.get("link") or item.get("product_link"),
                "raw_price": item_price
            })
        
        final_list.sort(key=lambda x: x['raw_price'])
        return jsonify({"results": final_list[:8]})

    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

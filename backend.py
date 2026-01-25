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

def get_match_score(original, target):
    """İki başlık arasındaki benzerliği puanlar (0-100)"""
    original_words = set(re.findall(r'\w+', original.lower()))
    target_words = set(re.findall(r'\w+', target.lower()))
    
    if not original_words: return 0
    common = original_words.intersection(target_words)
    return (len(common) / len(original_words)) * 100

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        original_title = data.get("title", "")
        current_price = parse_price(data.get("price", "0"))
        
        # ARAMA: En doğru sonuç için ilk 4-5 kelimeyi tırnak içinde göndererek Google'ı zorluyoruz
        brand_model = " ".join(original_title.split()[:5])
        
        params = {
            "engine": "google_shopping",
            "q": brand_model,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "num": "40"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        for item in results:
            item_title = item.get("title", "")
            item_price = parse_price(item.get("price"))
            actual_link = item.get("link") or item.get("product_link")

            if not actual_link or item_price == 0: continue

            # --- MİLYONLARCA ÜRÜN İÇİN GENEL MANTIK ---
            
            # 1. Benzerlik Puanı: Başlıkların en az %50'si örtüşmeli
            score = get_match_score(original_title, item_title)
            if score < 50: continue

            # 2. Fiyat Uçurumu (En Önemli Kriter):
            # Milyonlarca üründe değişmeyen kural: Bir ürünün asıl fiyatı ile 
            # "aksesuar/yedek parça" fiyatı arasında uçurum vardır.
            # %50'den daha ucuz olan ürün "BAŞKA BİR ŞEYDİR" (istisnalar hariç).
            if current_price > 500: # Ucuz ürünlerde esnek, pahalıda katı
                price_ratio = item_price / current_price
                if price_ratio < 0.50 or price_ratio > 2.0:
                    continue
            
            # 3. Spesifik Kelime Kontrolü (Hafıza, Set vb.)
            # Aranan üründe rakamsal bir değer (256GB, 2TB, 3'lü) varsa, sonuçta da olmalı.
            original_specs = re.findall(r'\d+\s*[gt]b|\d+[\s\-\']?li|\d+[\s\-\']?lü', original_title.lower())
            if original_specs:
                if not any(spec in item_title.lower() for spec in original_specs):
                    continue

            final_list.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": actual_link,
                "image": item.get("thumbnail"),
                "raw_price": item_price,
                "score": score
            })
        
        # Hem puana hem fiyata göre akıllı sıralama
        final_list.sort(key=lambda x: (-x['score'], x['raw_price']))
        
        return jsonify({"results": final_list[:8]})
        
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

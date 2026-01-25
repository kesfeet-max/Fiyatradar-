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
        
        # 1. ANALİZ: Ürün bir "SET" mi?
        is_set = any(word in original_title for word in ["set", "takım", "3'lü", "komple"])
        
        # Arama sorgusunu daralt (Marka + Model + Kritik Kelime)
        search_words = original_title.split()[:4]
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
        # Çok daha katı yasaklı listesi (Aksesuar koruması)
        forbidden = ["tel", "izgara", "yedek", "parça", "aksesuar", "filtre", "kitap", "dvd", "ikinci el"]

        for item in results:
            item_title = item.get("title", "").lower()
            item_price = parse_price(item.get("price"))
            
            # --- KRİTİK FİLTRELEME MANTIKLARI ---

            # A) SET KONTROLÜ (Screenshot_24 Çözümü):
            # Eğer asıl ürün SET ise ve bulunan üründe "set" kelimesi geçmiyorsa, bu parçadır. ELE!
            if is_set and not any(word in item_title for word in ["set", "takım", "3'lü"]):
                continue

            # B) FİYAT SAPMASI (Hayati Önem):
            # Gerçek ürünün fiyatından %40'tan fazla sapma varsa o ürün "başka bir şeydir".
            # 17.000 TL'lik set yerine 8.000 TL'lik sonuç gelirse otomatik elenir.
            if current_price > 0:
                deviation = abs(item_price - current_price) / current_price
                if deviation > 0.40: # %40'tan fazla fark varsa (çok ucuz veya çok pahalı)
                    continue

            # C) BAŞLIK EŞLEŞME PUANI:
            # Aranan kelimelerin en az %70'i başlıkta geçmeli.
            match_count = sum(1 for word in search_words if word.lower() in item_title)
            if match_count < len(search_words) * 0.7:
                continue

            final_list.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": item.get("link") or item.get("product_link"),
                "image": item.get("thumbnail"),
                "raw_price": item_price
            })
        
        final_list.sort(key=lambda x: x['raw_price'])
        return jsonify({"results": final_list[:6]})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

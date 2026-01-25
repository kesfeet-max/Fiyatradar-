import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

@app.route("/", methods=["GET"])
def home():
    return "Fiyat Bul Sunucusu Calisiyor!", 200

def parse_price(price_str):
    if not price_str: return 0
    try:
        # Fiyat metnindeki sayısal olmayan her şeyi temizler
        val = re.sub(r'[^\d]', '', str(price_str).split(',')[0])
        return int(val)
    except: return 0

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"results": [], "error": "Veri gonderilmedi"}), 400
            
        original_title = data.get("title", "").strip()
        
        # ARAMA STRATEJİSİ: 
        # Sadece ilk 3 kelime bazen çok genel kalıyor. 
        # Eğer başlıkta "Eğitim Seti" gibi kritik ibareler varsa onları da aramaya ekliyoruz.
        search_words = original_title.lower().split()[:4] # 4 kelimeye çıkardık
        search_query = " ".join(search_words)

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", 
            "gl": "tr",
            "num": "40" 
        }

        response = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        # Senin aradığın büyük setlerle karışabilecek küçük/yan ürünleri engelleme listesi
        forbidden = ["kılıf", "case", "cam", "film", "kapak", "yedek", "parça", "tamir", "dvd", "2.el", "ikinci el"]

        for item in results:
            item_title = item.get("title", "").lower()
            price_val = parse_price(item.get("price"))
            link = item.get("link") or item.get("product_link")

            # MODEL EŞLEŞME KONTROLÜ
            # Aranan ilk iki kelime (genelde marka ve model) mutlaka başlıkta geçmeli
            is_match = all(word in item_title for word in search_words[:2])

            # FİLTRELEME KURALLARI:
            # 1. Marka eşleşmeli
            # 2. Yasaklı kelime içermemeli
            # 3. 150 TL'den ucuz olmamalı (kargo bedeli veya çok alakasız küçük parçaları eler)
            if is_match and not any(f in item_title for f in forbidden) and price_val > 150:
                final_list.append({
                    "site": item.get("source"),
                    "price": item.get("price"),
                    "link": link,
                    "raw_price": price_val
                })
        
        # En ucuzdan pahalıya sırala
        final_list.sort(key=lambda x: x['raw_price'])
        
        # Eğer sonuç çoksa, en alakalı ilk 10 tanesini döndür
        return jsonify({"results": final_list[:10]})

    except Exception as e:
        print(f"Sunucu Hatasi: {str(e)}")
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    # Render ve yerel çalışma için dinamik port ayarı
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

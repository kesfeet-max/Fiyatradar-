import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os # Render portu için gerekli

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

# 1. YENİ: Ana Sayfa Rotası (404 hatasını engeller)
@app.route("/", methods=["GET"])
def home():
    return "Fiyat Bul Sunucusu Calisiyor!", 200

def parse_price(price_str):
    if not price_str: return 0
    try:
        # Fiyatı temizle ve sayıya çevir
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
        
        # Arama sorgusunu optimize et
        search_words = original_title.lower().split()[:3]
        search_query = " ".join(search_words)

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr",
            "num": "50" 
        }

        response = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        forbidden = ["kılıf", "case", "cam", "film", "kapak", "yedek", "parça", "tamir"]

        for item in results:
            item_title = item.get("title", "").lower()
            price_val = parse_price(item.get("price"))
            link = item.get("link") or item.get("product_link")

            # Birebir Model Kontrolü
            is_match = all(word in item_title for word in search_words)

            # Filtreleme: Yasaklı kelime yoksa ve 5000 TL üzerindeyse ekle
            if is_match and not any(f in item_title for f in forbidden) and price_val > 100:
                final_list.append({
                    "site": item.get("source"),
                    "price": item.get("price"),
                    "link": link,
                    "raw_price": price_val
                })
        
        final_list.sort(key=lambda x: x['raw_price'])
        return jsonify({"results": final_list[:8]})

    except Exception as e:
        print(f"Hata olustu: {str(e)}") # Loglarda hatayı görmek için
        return jsonify({"results": [], "error": str(e)})

# 2. KRİTİK DÜZENLEME: Render için Port Ayarı
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000)) # Render genelde 10000 kullanır
    app.run(host='0.0.0.0', port=port)


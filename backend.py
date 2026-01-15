import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

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
        original_title = data.get("title", "").strip()
        
        # 1. KRİTİK ADIM: Anahtar kelimeleri belirle (Örn: "iPhone", "17")
        # Marka ve model numarasını yakalamak için ilk 3 kelimeyi alıyoruz
        search_words = original_title.lower().split()[:3]
        search_query = " ".join(search_words)

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr",
            "num": "50" # Daha fazla tarama yaparak doğru modelin ucuzunu bulur
        }

        response = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        forbidden = ["kılıf", "case", "cam", "film", "kapak", "yedek", "parça", "tamir"]

        for item in results:
            item_title = item.get("title", "").lower()
            price_val = parse_price(item.get("price"))
            link = item.get("link") or item.get("product_link")

            # 2. KRİTİK ADIM: Birebir Model Kontrolü
            # Aranan kelimelerin HEPSİ başlıkta geçiyor mu? (Örn: "iPhone" ve "17")
            # Bu kontrol iPhone 14 veya 15'lerin listeye girmesini engeller
            is_match = all(word in item_title for word in search_words)

            if is_match and not any(f in item_title for f in forbidden) and price_val > 5000:
                final_list.append({
                    "site": item.get("source"),
                    "price": item.get("price"),
                    "link": link,
                    "raw_price": price_val
                })
        
        # En ucuzdan pahalıya sırala
        final_list.sort(key=lambda x: x['raw_price'])

        return jsonify({"results": final_list[:8]})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    app.run()

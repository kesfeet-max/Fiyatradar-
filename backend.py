import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def format_price(price_str):
    if not price_str: return 0
    try:
        # "123.999,00 TL" formatını sayıya çevirir
        cleaned = re.sub(r'[^\d]', '', str(price_str).split(',')[0])
        return int(cleaned)
    except: return 0

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        full_title = data.get("title", "")
        
        # Arama sorgusunu optimize et
        search_query = " ".join(full_title.split()[:5])

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr",
            "num": "30" # Daha geniş tarama yaparak 112.999 TL gibi fırsatları yakalar
        }

        response = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        # Yasaklı kelimeler (Yedek parça ve aksesuar engelleme)
        forbidden = ["kılıf", "case", "cam", "film", "kapak", "yedek", "parça", "tamir", "ekran koruyucu", "lens"]
        
        # Güvenilir ve popüler satıcı listesi
        whitelist = ["trendyol", "hepsiburada", "n11", "amazon", "vatan", "teknosa", "pazarama", "pttavm", "turkcell", "mediamarkt"]

        for item in results:
            title = item.get("title", "").lower()
            source = item.get("source", "").lower()
            price_val = format_price(item.get("price"))
            link = item.get("link") or item.get("product_link")

            # FİLTRELEME: Aksesuar değilse ve fiyatı mantıklıysa (Telefon için > 5000 TL)
            if not any(word in title for word in forbidden) and price_val > 5000:
                if any(w in source for w in whitelist) and link:
                    final_list.append({
                        "site": item.get("source"),
                        "price": item.get("price"),
                        "link": link,
                        "raw_price": price_val
                    })
        
        # EN ÖNEMLİ KISIM: Fiyata göre artan sıralama (En ucuz en üstte)
        final_list.sort(key=lambda x: x['raw_price'])

        return jsonify({"results": final_list[:8]}) # Kullanıcıya en iyi 8 sonucu sunar
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    app.run()

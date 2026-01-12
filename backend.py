import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

@app.route("/", methods=["GET", "HEAD"])
def home():
    return "Fiyat Radarı Sistemi Aktif!"

def clean_price(price_str):
    if not price_str: return 0.0
    try:
        cleaned = str(price_str).replace('TL', '').replace('₺', '').replace(' ', '')
        if ',' in cleaned and '.' in cleaned:
            cleaned = cleaned.replace('.', '')
        cleaned = cleaned.replace(',', '.')
        return float(re.sub(r'[^\d.]', '', cleaned))
    except:
        return 0.0

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        full_title = data.get("title", "")
        
        # ZAMAN AŞIMI ÇÖZÜMÜ: Sadece en önemli 2-3 kelimeyi alarak aramayı hızlandırıyoruz
        # Örn: "Sony Playstation 5 Slim Digital" -> "Sony Playstation 5"
        clean_title = re.sub(r'[^\w\s]', '', full_title)
        words = clean_title.split()
        search_query = " ".join(words[:3]) 
        
        params = {
            "engine": "google_shopping",
            "q": search_query,
            "hl": "tr", "gl": "tr",
            "api_key": SERP_API_KEY
        }

        # Render ücretsiz tier zaman aşımını önlemek için timeout süresini optimize ettik
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=8)
        results = response.json().get("shopping_results", [])
        
        output = []
        # Sadece en bilinen siteleri filtrele
        whitelist = ["trendyol", "hepsiburada", "n11", "amazon", "vatan", "teknosa", "pazarama"]

        for item in results:
            source = item.get("source", "").lower()
            link = item.get("link")
            if any(w in source for w in whitelist) and link:
                output.append({
                    "site": item.get("source"),
                    "price": item.get("price"),
                    "link": link,
                    "p_val": clean_price(item.get("price"))
                })
        
        # En düşük fiyatı en üste al
        output.sort(key=lambda x: x['p_val'])
        for x in output: del x['p_val']

        return jsonify({"results": output[:5]})
    except Exception as e:
        return jsonify({"results": [], "error": "Zaman aşımı veya hata oluştu."})

if __name__ == "__main__":
    app.run()

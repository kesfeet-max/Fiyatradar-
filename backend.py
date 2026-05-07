import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
from urllib.parse import urlparse, parse_qs, unquote

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_price(price_str):
    if not price_str or price_str == "0": return 0
    try:
        s = str(price_str).replace('TL', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        s = re.sub(r'[^\d.]', '', s)
        return float(s)
    except:
        return 0

def extract_direct_url(google_url):
    """Google'ın yönlendirme linkinden gerçek mağaza linkini çıkarır."""
    if not google_url: return ""
    if "google.com/url" in google_url:
        parsed_url = urlparse(google_url)
        # 'q' veya 'url' parametresini ara
        query_params = parse_qs(parsed_url.query)
        actual_url = query_params.get('q') or query_params.get('url')
        if actual_url:
            return unquote(actual_url[0])
    return google_url

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok"}), 200

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200
    try:
        data = request.get_json()
        title = data.get("title", "")
        current_price = clean_price(data.get("price", "0"))
        
        params = {
            "engine": "google_shopping",
            "q": title,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "direct_link": True
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        for item in results:
            p_val = clean_price(item.get("price", "0"))
            
            # Aksesuar ve uçuk fiyat filtresi
            if current_price > 0:
                if p_val > (current_price * 1.5) or p_val < (current_price * 0.4): continue
            
            # LİNK TEMİZLEME BURADA YAPILIYOR
            raw_link = item.get("link") or item.get("product_link") or ""
            direct_link = extract_direct_url(raw_link)

            final_list.append({
                "site": item.get("source", "Mağaza"),
                "price": item.get("price"),
                "price_value": p_val,
                "image": item.get("thumbnail"),
                "link": direct_link, # Artık temizlenmiş link gidiyor
                "title": item.get("title")
            })
        
        final_list.sort(key=lambda x: x['price_value'] if x['price_value'] > 0 else 999999)
        return jsonify({"results": final_list})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

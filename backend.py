import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os
from urllib.parse import urlparse, parse_qs, unquote

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def parse_price(price_str):
    if not price_str: return 0
    try:
        val = re.sub(r'[^\d]', '', str(price_str).split(',')[0])
        return int(val)
    except: return 0

def clean_vendor_url(raw_url):
    """Google'ın reklam linkinden gerçek mağaza (Trendyol, HB, Amazon vb.) linkini söker."""
    if not raw_url: return ""
    try:
        if "google.com" in raw_url:
            parsed = urlparse(raw_url)
            queries = parse_qs(parsed.query)
            # Google linklerinde gerçek adres genellikle 'adurl' veya 'url' içindedir
            actual = queries.get('adurl', [None])[0] or queries.get('url', [None])[0]
            if actual:
                actual = unquote(actual)
                # Linkin sonundaki reklam takip kodlarını (?) temizle
                return actual.split('?')[0]
    except:
        pass
    return raw_url

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        original_title = data.get("title", "").lower()
        current_price = parse_price(data.get("price", "0"))
        
        params = {
            "engine": "google_shopping",
            "q": original_title,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "num": "20"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        forbidden = {"kordon", "kayış", "silikon", "kılıf", "koruyucu", "cam", "aksesuar", "yedek"}

        for item in results:
            item_title = item.get("title", "").lower()
            item_price = parse_price(item.get("price"))
            source = item.get("source", "")
            
            if item_price == 0: continue
            if any(f in item_title for f in forbidden) and not any(f in original_title for f in forbidden): continue

            # LİNK ONARMA İŞLEMİ (Tüm siteler için geçerli)
            raw_link = item.get("link", "")
            direct_product_link = clean_vendor_url(raw_link)

            final_list.append({
                "site": source,
                "price": item.get("price"),
                "image": item.get("thumbnail"),
                "raw_price": item_price,
                "link": direct_product_link 
            })
        
        final_list.sort(key=lambda x: x['raw_price'])
        return jsonify({"results": final_list[:10]})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

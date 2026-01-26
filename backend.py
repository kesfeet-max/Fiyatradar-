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

def extract_clean_link(google_url):
    """Google yönlendirmesini sunucu tarafında çözer."""
    if not google_url: return ""
    try:
        # 1. Adım: URL içindeki 'adurl' veya 'url' parametresini ayıkla
        parsed = urlparse(google_url)
        queries = parse_qs(parsed.query)
        actual_url = queries.get('adurl', [None])[0] or queries.get('url', [None])[0] or queries.get('q', [None])[0]
        
        if actual_url:
            actual_url = unquote(actual_url)
            # 2. Adım: Eğer link hala bir Google yönlendirmesiyse (iç içe geçmişse) temizle
            if "google.com" in actual_url and "url=" in actual_url:
                return extract_clean_link(actual_url)
            return actual_url.split('?')[0] # Takip kodlarını atar, saf ürün linkini bırakır
    except:
        pass
    return google_url

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
            "hl": "tr", "gl": "tr", "num": "15"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        forbidden = {"kordon", "kayış", "silikon", "kılıf", "koruyucu", "cam", "yedek", "parça", "aparat", "aksesuar"}

        for item in results:
            item_title = item.get("title", "").lower()
            item_price = parse_price(item.get("price"))
            
            if item_price == 0: continue
            if any(f in item_title for f in forbidden) and not any(f in original_title for f in forbidden): continue

            # LİNK BURADA TEMİZLENİYOR
            raw_link = item.get("link", "")
            safe_link = extract_clean_link(raw_link)

            final_list.append({
                "site": item.get("source", "Mağaza"),
                "price": item.get("price"),
                "image": item.get("thumbnail"),
                "link": safe_link
            })
        
        return jsonify({"results": final_list})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os
from urllib.parse import urlparse, parse_qs, unquote

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_google_url(url):
    """Google sarmalını Python tarafında çözer."""
    if not url: return ""
    if "google.com/url?" in url or "google.com.tr/url?" in url:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        # url, adurl veya q parametrelerinden birini al
        cleaned = params.get('url') or params.get('adurl') or params.get('q')
        if cleaned:
            return unquote(cleaned[0])
    return url

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
        
        search_query = " ".join(original_title.split()[:5])

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        forbidden = {"kordon", "kayış", "kılıf", "aksesuar", "yedek"}

        for item in results:
            item_title = item.get("title", "").lower()
            item_price = parse_price(item.get("price"))
            # Önce direct_link'i dene, yoksa normal linki al
            raw_link = item.get("direct_link") or item.get("link")

            if not raw_link or item_price == 0: continue
            
            # Linki temizle
            clean_link = clean_google_url(raw_link)

            # Filtreler (Mevcut mantığın)
            if current_price > 500 and item_price < (current_price * 0.50): continue
            if any(f in item_title for f in forbidden) and not any(f in original_title for f in forbidden): continue

            final_list.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": clean_link, # Artık burası tertemiz
                "image": item.get("thumbnail"),
                "raw_price": item_price
            })
        
        final_list.sort(key=lambda x: x['raw_price'])
        unique_results = []
        seen_sites = set()
        for res in final_list:
            if res['site'] not in seen_sites:
                unique_results.append(res)
                seen_sites.add(res['site'])

        return jsonify({"results": unique_results[:10]})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

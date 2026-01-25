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

def clean_direct_link(google_link):
    """Google'ın yönlendirme linkinden asıl mağaza linkini çıkarır."""
    if not google_link:
        return ""
    
    # Eğer link zaten bir mağaza linkiyse dokunma
    if "google.com" not in google_link:
        return google_link
        
    try:
        parsed_url = urlparse(google_link)
        params = parse_qs(parsed_url.query)
        
        # Google Shopping linklerinde asıl hedef genellikle 'adurl' veya 'url' parametresindedir
        actual_url = params.get('adurl') or params.get('url')
        
        if actual_url:
            return unquote(actual_url[0])
    except:
        pass
    
    return google_link

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        original_title = data.get("title", "").lower()
        current_price = parse_price(data.get("price", "0"))
        
        words = original_title.split()
        search_query = " ".join(words[:5])

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "num": "60"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        forbidden = {"kordon", "kayış", "silikon", "kılıf", "koruyucu", "cam", "yedek", "parça", "aparat", "aksesuar", "kitap"}

        for item in results:
            item_title = item.get("title", "").lower()
            item_price = parse_price(item.get("price"))
            
            # 1. ADIM: Linki Temizle (Google katmanını soy)
            raw_link = item.get("product_link") or item.get("link")
            direct_link = clean_direct_link(raw_link)
            
            if not direct_link: continue

            # 2. ADIM: Başarılı olan Fiyat/Aksesuar Filtremiz (Bunu bozmadım)
            if current_price > 2000 and item_price < (current_price * 0.60): continue
            if any(f in item_title for f in forbidden) and not any(f in original_title for f in forbidden):
                continue

            final_list.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": direct_link, # Artık temiz ve direkt link
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
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

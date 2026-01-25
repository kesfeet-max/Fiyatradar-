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

def extract_model_code(title):
    codes = re.findall(r'[A-Z0-9]+\s?[A-Z0-9]*', title.upper())
    return [c for c in codes if len(c) > 2 and any(char.isdigit() for char in c)]

def get_real_url(google_url):
    """Google'ın reklam linkini soyup gerçek ürün linkini çıkarır."""
    try:
        if "google.com/url?" in google_url:
            parsed = urlparse(google_url)
            # adurl parametresi genellikle gerçek ürün linkidir
            actual = parse_qs(parsed.query).get('adurl', [None])[0] or \
                     parse_qs(parsed.query).get('url', [None])[0]
            if actual:
                # Linkin içindeki takip kodlarını temizle (?merchantId=... gibi)
                return unquote(actual).split('?')[0]
    except:
        pass
    return google_url

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        original_title = data.get("title", "").lower()
        current_price = parse_price(data.get("price", "0"))
        
        # Arama terimini daha spesifik yapıyoruz
        search_query = f"{original_title}"

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "num": "20"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        forbidden = {"kordon", "kayış", "silikon", "kılıf", "koruyucu", "cam", "yedek", "parça", "aparat", "aksesuar", "kitap", "teli", "askı", "sticker"}

        for item in results:
            item_title = item.get("title", "").lower()
            item_price = parse_price(item.get("price"))
            source = item.get("source", "")
            google_link = item.get("link", "")
            
            if item_price == 0: continue
            
            # Senin filtrelerin
            if current_price > 2000:
                if item_price < (current_price * 0.60): continue
            elif current_price > 500:
                if item_price < (current_price * 0.50): continue

            if any(f in item_title for f in forbidden) and not any(f in original_title for f in forbidden):
                continue

            # --- KRİTİK DÜZELTME ---
            real_link = get_real_url(google_link)

            final_list.append({
                "site": source,
                "price": item.get("price"),
                "image": item.get("thumbnail"),
                "raw_price": item_price,
                "link": real_link # Artık eklentiye 'saf' link gidiyor
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

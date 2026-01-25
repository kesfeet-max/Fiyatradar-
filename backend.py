import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os
from urllib.parse import unquote

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

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        original_title = data.get("title", "").lower()
        current_price = parse_price(data.get("price", "0"))
        
        words = original_title.split()
        search_query = " ".join(words[:5])
        model_codes = extract_model_code(original_title)

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "num": "60"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        forbidden = {"kordon", "kayış", "silikon", "kılıf", "koruyucu", "cam", "yedek", "parça", "aparat", "aksesuar", "kitap", "teli", "askı", "sticker"}

        for item in results:
            item_title = item.get("title", "").lower()
            item_price = parse_price(item.get("price"))
            
            # --- AGRESİF LİNK TEMİZLEME ---
            link = item.get("direct_link") or item.get("link") or item.get("product_link") or ""
            
            if "google.com" in link:
                # Linkin içindeki 'q=' veya 'url=' sonrasını yakala
                found = re.search(r'(?:url|q|adurl)=([^&]+)', link)
                if found:
                    link = unquote(found.group(1))
                
                # Eğer hala içinde google varsa, linki http üzerinden temizle
                if "google.com" in link and "http" in link:
                    link = "http" + link.split("http")[-1]

            if not link or item_price == 0: continue

            # --- SENİN ÇALIŞAN FİLTRELERİN ---
            if current_price > 2000:
                if item_price < (current_price * 0.60): continue
            elif current_price > 500:
                if item_price < (current_price * 0.50): continue

            if model_codes:
                if not any(code.lower() in item_title for code in model_codes[:2]):
                    continue

            if any(f in item_title for f in forbidden) and not any(f in original_title for f in forbidden):
                continue

            final_list.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": link,
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

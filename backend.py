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
    except:
        return 0

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        search_query = data.get("title", "")
        
        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        shopping_results = response.json().get("shopping_results", [])
        
        final_list = []
        for item in shopping_results:
            # 1. HAM LİNKİ AL
            link = item.get("direct_link") or item.get("link") or ""
            
            # 2. RADİKAL TEMİZLİK: 'q=' GÖRDÜĞÜN ANDA ÖNCESİNİ SİL
            if "google.com/url?" in link:
                if "q=" in link:
                    link = link.split("q=")[1].split("&")[1] if "&" in link.split("q=")[1] else link.split("q=")[1]
                elif "url=" in link:
                    link = link.split("url=")[1].split("&")[0]

            # 3. ÇİFT KATMANLI DECODE (Karakter hatalarını %100 çözer)
            clean_link = unquote(unquote(link))

            final_list.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": clean_link,
                "image": item.get("thumbnail"),
                "raw_price": parse_price(item.get("price"))
            })
        
        final_list.sort(key=lambda x: x['raw_price'])
        return jsonify({"results": final_list[:10]})

    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

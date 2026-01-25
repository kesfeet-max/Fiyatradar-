import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os
from urllib.parse import urlparse, parse_qs, unquote

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def final_destination_url(url):
    """Google'ın iç içe geçmiş yönlendirmelerini tek hamlede çözer."""
    if not url: return ""
    if "adurl" in url or "url=" in url or "q=" in url:
        try:
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            # Google'ın asıl linki sakladığı 3 ana parametre
            potential_link = params.get('adurl') or params.get('url') or params.get('q')
            if potential_link:
                return unquote(potential_link[0])
        except:
            return url
    return url

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        original_title = data.get("title", "").lower()
        
        # Arama sorgusunu daraltalım ki sonuç bulma şansı artsın
        search_query = " ".join(original_title.split()[:4])

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        for item in results:
            raw_link = item.get("link") or item.get("product_link")
            if not raw_link: continue

            # LİNKİ BURADA TEMİZLİYORUZ
            clean_link = final_destination_url(raw_link)

            final_list.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": clean_link,
                "image": item.get("thumbnail"),
                "raw_price": re.sub(r'[^\d]', '', str(item.get("price")).split(',')[0])
            })
        
        return jsonify({"results": final_list[:10]})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

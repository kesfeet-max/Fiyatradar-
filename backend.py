import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
from urllib.parse import urlparse, parse_qs, unquote

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def get_direct_vendor_url(google_url):
    """Google'ın reklam URL'sini parçalar ve saf linki bulur."""
    try:
        if "google.com" in google_url:
            parsed = urlparse(google_url)
            queries = parse_qs(parsed.query)
            # adurl veya url parametreleri genellikle gerçek ürün linkidir
            actual = queries.get('adurl', [None])[0] or queries.get('url', [None])[0]
            if actual:
                actual = unquote(actual)
                # Takip kodlarını (?) silerek saf ürün linkini bırakır
                return actual.split('?')[0]
    except:
        pass
    return google_url

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        original_title = data.get("title", "")
        
        params = {
            "engine": "google_shopping",
            "q": original_title,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        for item in results:
            raw_link = item.get("link", "")
            # --- HATALARI BİTİREN KISIM ---
            # Google linkini ayıklayıp doğrudan mağaza linkine dönüştürüyoruz
            clean_link = get_direct_vendor_url(raw_link)

            final_list.append({
                "site": item.get("source", ""),
                "price": item.get("price"),
                "image": item.get("thumbnail"),
                "link": clean_link,
                "title": item.get("title")
            })
        
        return jsonify({"results": final_list[:10]})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

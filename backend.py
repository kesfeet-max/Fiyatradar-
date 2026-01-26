import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def resolve_final_url(google_url):
    """Google linkini takip eder ve ulaştığı son gerçek mağaza linkini döndürür."""
    try:
        # User-agent ekleyerek bot engelini aşıyoruz
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        # allow_redirects=True sayesinde Google'ın yönlendirdiği son noktaya ulaşırız
        response = requests.head(google_url, headers=headers, allow_redirects=True, timeout=3)
        final_url = response.url
        
        # Eğer hala google içindeyse linki temizle
        if "google.com/url" in final_url:
            from urllib.parse import urlparse, parse_qs, unquote
            parsed = urlparse(final_url)
            actual = parse_qs(parsed.query).get('adurl', [None])[0] or parse_qs(parsed.query).get('url', [None])[0]
            return unquote(actual) if actual else final_url
        
        return final_url.split('?')[0] # Reklam takip kodlarını (?) atar
    except:
        return google_url

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
        results = response.json().get("shopping_results", [])
        
        final_list = []
        for item in results[:6]: # İlk 6 en alakalı sonucu alıyoruz (Hız için)
            raw_url = item.get("link")
            # --- YENİ YÖNTEM: LİNKİ SUNUCUDA ÇÖZ ---
            direct_link = resolve_final_url(raw_url)
            
            final_list.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "image": item.get("thumbnail"),
                "link": direct_link # Eklentiye giden link artık %100 saf mağaza linki
            })
        
        return jsonify({"results": final_list})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

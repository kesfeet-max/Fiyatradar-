import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def parse_price(price_str):
    if not price_str: return 0
    try:
        val = re.sub(r'[^\d]', '', str(price_str).split(',')[0])
        return int(val)
    except: return 0

def extract_must_have(text):
    """Hafıza ve Kritik model kelimelerini ayıklar."""
    # GB, TB, Pro, Max, Ultra gibi kelimeleri bul
    must_have = re.findall(r'(\d+\s*[gt]b|pro\s*max|ultra|plus)', text.lower())
    return must_have

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        original_title = data.get("title", "").lower()
        current_price = parse_price(data.get("price", "0"))
        
        # 1. ANALİZ: Kritik kelimeler (2TB, Pro Max vb.)
        required_words = extract_must_have(original_title)
        
        # Arama sorgusunu biraz daha genişletelim (Google daha çok sonuç getirsin)
        search_query = " ".join(original_title.split()[:6])

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "num": "35"
        }

        results = requests.get("https://serpapi.com/search.json", params=params).json().get("shopping_results", [])
        
        final_list = []
        forbidden = ["kordon", "kutu", "yedek", "parça", "ikinci el", "kılıf"]

        for item in results:
            item_title = item.get("title", "").lower()
            item_price = parse_price(item.get("price"))

            # --- SÜPER FİLTRE ---
            
            # A) KRİTİK KELİME KONTROLÜ (Hafıza tutmuyorsa asla gösterme!)
            if not all(word in item_title for word in required_words):
                continue

            # B) FİYAT SAPMA KONTROLÜ (Saatteki gibi sonuç gelmeme sorunu için %50'ye esnetelim)
            if current_price > 0:
                deviation = abs(item_price - current_price) / current_price
                if deviation > 0.50: # %50 fark varsa ele (Hala güvenli ama daha esnek)
                    continue

            # C) YASAKLI KELİME
            if any(f in item_title for f in forbidden) and not any(f in original_title for f in forbidden):
                continue

            final_list.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": item.get("link"),
                "image": item.get("thumbnail"),
                "raw_price": item_price
            })
        
        final_list.sort(key=lambda x: x['raw_price'])
        return jsonify({"results": final_list[:8]})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

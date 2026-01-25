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
        # Fiyatı temizle ve sayıya çevir (Örn: 134.116,00 -> 134116)
        val = re.sub(r'[^\d]', '', str(price_str).split(',')[0])
        return int(val)
    except: return 0

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        original_title = data.get("title", "").lower()
        # İNCELENEN ÜRÜNÜN GERÇEK FİYATI
        current_price = parse_price(data.get("price", "0"))
        
        # 1. KURAL: Çok spesifik arama yap (Tırnak içinde arama Google'da daha nettir)
        search_query = " ".join(original_title.split()[:5])

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "num": "30"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        for item in results:
            item_title = item.get("title", "").lower()
            item_price = parse_price(item.get("price"))
            
            # --- ZORUNLU FİLTRELER (YATIRIMCI KORUMASI) ---

            # A) FİYAT UÇURUMU KONTROLÜ (GÜVENLİK DUVARI)
            # Eğer bulunan ürün, incelenen üründen %60'dan daha ucuzsa (134k vs 14k)
            # Bu ürün kesinlikle ya çakmadır, ya kordondur ya da hatadır. GÖSTERME!
            if current_price > 1000: # Sadece 1000 TL üstü değerli ürünlerde korumayı aç
                min_threshold = current_price * 0.40 # Fiyatın en az %40'ı olmalı
                if item_price < min_threshold:
                    continue

            # B) KELİME ANALİZİ (Gelişmiş)
            # Aranan anahtar kelimelerin (Marka + Model) en az %80'i başlıkta olmalı
            search_keywords = original_title.split()[:3] # Örn: ["Seiko", "1", "Prospex"]
            if not all(k in item_title for k in search_keywords):
                continue

            final_list.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": item.get("link"),
                "image": item.get("thumbnail"),
                "raw_price": item_price
            })
        
        # Gerçekten ucuzdan pahalıya sırala
        final_list.sort(key=lambda x: x['raw_price'])
        
        return jsonify({"results": final_list[:8]})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

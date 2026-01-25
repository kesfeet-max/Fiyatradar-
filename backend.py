import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import os

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def extract_specifications(text):
    """Başlıktan GB, TB, Pro, Max gibi kritik özellikleri ayıklar."""
    specs = []
    # GB veya TB değerlerini yakala (Örn: 128GB, 256 gb, 2TB)
    capacity = re.findall(r'(\d+\s*[gt]b)', text.lower())
    if capacity:
        specs.extend(capacity)
    
    # Model spesifik kelimeleri yakala
    models = ["pro max", "pro", "plus", "ultra"]
    for m in models:
        if m in text.lower():
            specs.append(m)
            break # Pro Max varsa Pro'yu ayrıca ekleme
    return specs

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        original_title = data.get("title", "").lower()
        current_price = int(re.sub(r'[^\d]', '', data.get("price", "0").split(',')[0]))
        
        # --- KRİTİK: Teknik Özellikleri Kilitle ---
        required_specs = extract_specifications(original_title)
        
        params = {
            "engine": "google_shopping",
            "q": original_title, # Sorguyu olduğu gibi gönderiyoruz
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "num": "30"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        for item in results:
            item_title = item.get("title", "").lower()
            item_price = int(re.sub(r'[^\d]', '', item.get("price", "0").split(',')[0]))

            # 1. KURAL: TEKNİK ÖZELLİK KONTROLÜ (2TB varsa 2TB olmalı!)
            # Eğer orijinalde "2tb" varsa ama sonuçta yoksa, o ürün çöptür.
            if not all(spec in item_title for spec in required_specs):
                continue

            # 2. KURAL: FİYAT BANDI (Aşırı sapanları ele)
            # iPhone'da %20'den fazla ucuz olması imkansızdır (başka modeldir).
            if current_price > 0:
                deviation = abs(item_price - current_price) / current_price
                if deviation > 0.25: # iPhone'lar için daha dar bir limit (%25)
                    continue

            final_list.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": item.get("link"),
                "image": item.get("thumbnail"),
                "raw_price": item_price
            })
        
        # En ucuz gerçek sonuçları getir
        final_list.sort(key=lambda x: x['raw_price'])
        return jsonify({"results": final_list[:8]})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

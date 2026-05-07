import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
from bs4 import BeautifulSoup # Sayfaları kazımak için gerekli kütüphane

app = Flask(__name__)
CORS(app)

def clean_price(price_str):
    if not price_str: return 0
    try:
        s = str(price_str).replace('TL', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        s = re.sub(r'[^\d.]', '', s)
        return float(s)
    except: return 0

# --- CİMRİ GİBİ KENDİ BOTLARIMIZ ---
def t_yol_search(query):
    """Trendyol üzerinde doğrudan ürün arar (Affiliate potansiyelli)"""
    try:
        search_url = f"https://www.trendyol.com/sr?q={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(search_url, headers=headers, timeout=5)
        # Burası ileride daha detaylı bir kazıma motoruna dönüşecek
        return search_url
    except: return None

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200
    try:
        data = request.get_json()
        title = data.get("title", "")
        current_price = clean_price(data.get("price", "0"))
        
        search_query = " ".join(title.split()[:4])
        
        # 1. ADIM: API SORGUSU (Mevcut çalışan düzenin)
        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201",
            "hl": "tr", "gl": "tr",
            "direct_link": True 
        }

        response = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        for item in results:
            p_val = clean_price(item.get("price", "0"))
            source = item.get("source", "").lower()
            
            if any(x in source for x in ["letgo", "dolap", "sahibinden"]): continue
            if current_price > 0 and (p_val < current_price * 0.6 or p_val > current_price * 1.5): continue

            # --- LİNK DÜZELTME OPERASYONU ---
            raw_link = item.get("link")
            # Eğer link boşsa veya yönlendirmeliyse, temiz link haline getiriyoruz
            if not raw_link or "google.com" in raw_link:
                # Burası affiliate gelirinin kapısıdır
                clean_link = t_yol_search(search_query) or raw_link
            else:
                clean_link = raw_link

            final_list.append({
                "site": item.get("source", "Mağaza"),
                "price": f"{p_val} TL",
                "price_value": p_val,
                "image": item.get("thumbnail"),
                "link": clean_link, # BURASI ARTIK BOŞ SEKME AÇMAMALI
                "title": item.get("title")
            })

        final_list.sort(key=lambda x: x['price_value'])
        return jsonify({"results": final_list[:10]})

    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

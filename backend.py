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

def get_keywords(text):
    """Metinden marka, model ve önemli teknik terimleri ayıklar."""
    clean = re.sub(r'[^\w\s]', '', text.lower())
    words = clean.split()
    # İlk 5 kelime genelde en belirleyici olandır
    return words[:5]

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        original_title = data.get("title", "")
        current_price = parse_price(data.get("price", "0"))
        
        keywords = get_keywords(original_title)
        search_query = " ".join(keywords)

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "num": "60"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_results = []
        # Saat ve elektronik için tehlikeli 'aksesuar' kelimeleri
        trash_words = {
            "kordon", "kayış", "silikon", "kılıf", "koruyucu", "cam", 
            "yedek", "parça", "aparat", "aksesuar", "kitap", "teli", "askı"
        }

        for item in results:
            item_title = item.get("title", "").lower()
            item_price = parse_price(item.get("price"))
            link = item.get("link") or item.get("product_link")

            if not link or item_price == 0: continue

            # 1. ANALİZ: Kelime Eşleşme Puanı
            matches = sum(1 for k in keywords if k in item_title)
            match_score = matches / len(keywords) if keywords else 0

            # 2. KRİTİK FİLTRELER
            # A) Kelime Uyumu (Yarıdan fazlası tutmalı)
            if match_score < 0.55: continue

            # B) FİYAT DUVARI (Saat kordonu engelleyici)
            # Eğer ürün 500 TL üzerindeyse, bakılan fiyattan %50 ucuz olamaz.
            # (10.000 TL saate 5.000 TL altı ürün gelemez)
            if current_price > 500:
                if item_price < (current_price * 0.50):
                    continue

            # C) ÇÖP KELİME KONTROLÜ
            # Orijinal başlıkta 'kordon' yoksa ama sonuçta varsa ele.
            if any(tw in item_title for tw in trash_words) and not any(tw in original_title.lower() for tw in trash_words):
                continue

            final_results.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": link,
                "image": item.get("thumbnail"),
                "raw_price": item_price,
                "score": match_score
            })
        
        # Puan (Doğruluk) öncelikli, sonra en ucuz fiyat sıralaması
        final_results.sort(key=lambda x: (-x['score'], x['raw_price']))
        
        # Site tekrarlarını temizle (Aynı fiyata 5 tane Hepsiburada gelmesin)
        seen_sites = set()
        unique_results = []
        for res in final_results:
            if res['site'] not in seen_sites:
                unique_results.append(res)
                seen_sites.add(res['site'])

        return jsonify({"results": unique_results[:10]})
        
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

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

def get_clean_words(text):
    """Metni temizler ve kelime kümesine (set) çevirir."""
    # Gereksiz kısa kelimeleri ve bağlaçları atar
    words = re.findall(r'\w+', text.lower())
    return set([w for w in words if len(w) > 1])

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        original_title = data.get("title", "")
        current_price = parse_price(data.get("price", "0"))
        
        # 1. ADIM: Orijinal başlığı kelime torbasına çevir
        original_words = get_clean_words(original_title)
        
        # Arama için ilk 5 anahtar kelimeyi kullan (Google kısıtı nedeniyle)
        search_query = " ".join(list(original_words)[:6])

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "num": "50"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []
        # Parça/Aksesuar/Kitap engelleyici yasaklı kelimeler
        forbidden = {"kitap", "kılıf", "koruyucu", "yedek", "parça", "aparat", "aksesuar", "ikinci", "kordon"}

        for item in results:
            item_title = item.get("title", "")
            item_price = parse_price(item.get("price"))
            actual_link = item.get("link") or item.get("product_link")

            if not actual_link or item_price == 0: continue

            # 2. ADIM: Kelime Eşleşme Analizi (Sıralama Bağımsız)
            item_words = get_clean_words(item_title)
            
            # Orijinal başlıktaki kelimelerin kaç tanesi gelen sonuçta var?
            common_words = original_words.intersection(item_words)
            match_ratio = len(common_words) / len(original_words) if original_words else 0

            # --- CIMRI GİBİ KATI DOĞRULAMA ---

            # A) Kelime Eşleşme Oranı: Başlığın en az %60'ı (önemli kelimeler) tutmalı
            if match_ratio < 0.60:
                continue

            # B) Fiyat Bariyeri: Eğer bulunan ürün bakılanın %40'ından ucuzsa (8000 vs 3000)
            # Bu kesinlikle başka bir üründür (Örn: Kitap veya Cam).
            if current_price > 500:
                if item_price < (current_price * 0.45):
                    continue

            # C) Ters Kontrol: Eğer aranan üründe "kitap" yoksa ama sonuçta varsa ele
            if any(f in item_words for f in forbidden) and not any(f in original_words for f in forbidden):
                continue

            final_list.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": actual_link,
                "image": item.get("thumbnail"),
                "raw_price": item_price,
                "match": int(match_ratio * 100)
            })
        
        # Hem fiyata hem de eşleşme kalitesine göre sırala
        final_list.sort(key=lambda x: x['raw_price'])
        
        return jsonify({"results": final_list[:12]})
        
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

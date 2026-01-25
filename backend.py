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
    """Metni en önemli 3-4 anahtar kelimeye indirger."""
    clean = re.sub(r'[^\w\s]', '', text.lower())
    words = clean.split()
    # İlk 4 kelime genellikle Marka + Model'dir ve en önemli kısımdır.
    return words[:5]

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        original_title = data.get("title", "")
        current_price = parse_price(data.get("price", "0"))
        
        # ANAHTAR KELİME TABANLI ARAMA
        keywords = get_keywords(original_title)
        search_query = " ".join(keywords)

        params = {
            "engine": "google_shopping",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "num": "60" # Daha geniş tarama (60 sonuç)
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_results = []
        # Parça/Aksesuar/Kitap engelleyiciler
        trash_words = {"kitap", "kılıf", "koruyucu", "yedek", "parça", "aparat", "aksesuar", "ikinci", "kordon", "teli"}

        for item in results:
            item_title = item.get("title", "").lower()
            item_price = parse_price(item.get("price"))
            link = item.get("link") or item.get("product_link")

            if not link or item_price == 0: continue

            # 1. PUANLAMA: Orijinal anahtar kelimelerin kaçı başlıkta geçiyor?
            matches = sum(1 for k in keywords if k in item_title)
            match_score = matches / len(keywords) if keywords else 0

            # 2. KRİTİK FİLTRELER
            # A) Eğer anahtar kelimelerin yarısı bile yoksa bu ürün yanlıştır.
            if match_score < 0.50: continue

            # B) Fiyat Koruması (Uçurum Koruma): 
            # 5000 TL'lik üründe 100 TL'lik kitapları eler, ama 4290 TL'lik n11'i elimez.
            if current_price > 1000:
                if item_price < (current_price * 0.40): continue

            # C) Manuel Engelleme: Başlıkta çöp kelime varsa ve orijinalde yoksa ele.
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
        
        # SIRALAMA: Önce en yüksek eşleşme puanı, sonra en düşük fiyat
        final_results.sort(key=lambda x: (-x['score'], x['raw_price']))
        
        return jsonify({"results": final_results[:10]})
        
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

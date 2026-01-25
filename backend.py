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

@app.route("/compare", methods=["POST"])
def compare():
    try:
        data = request.get_json()
        original_title = data.get("title", "").lower()
        current_price = parse_price(data.get("price", "0"))
        
        # 1. ADIM: Arama Sorgusunu Tırnak İçine Al (Birebir eşleşme için Google'ı zorlar)
        # Sadece Marka ve Model'i alıyoruz.
        words = original_title.split()
        brand_model = " ".join(words[:4])
        
        params = {
            "engine": "google_shopping",
            "q": f'"{brand_model}"', # Tırnak ekledik: Mutlaka bu kelimeler geçmeli
            "api_key": SERP_API_KEY,
            "hl": "tr", "gl": "tr", "num": "50"
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        results = response.json().get("shopping_results", [])
        
        final_list = []

        for item in results:
            item_title = item.get("title", "").lower()
            item_price = parse_price(item.get("price"))
            actual_link = item.get("link") or item.get("product_link")

            if not actual_link or item_price == 0: continue

            # --- MİLYONLARCA ÜRÜN İÇİN EVRENSEL FİLTRELER ---

            # A) FİYAT BARİYERİ (Kitap/Aksesuar Engelleyici)
            # Eğer bulunan ürün, aranan üründen %70 daha ucuzsa (8000 TL vs 26 TL)
            # Bu kesinlikle yanlış kategoridir (Kitap, kılıf, yedek parça). GÖSTERME!
            if current_price > 200: # Çok ucuz ürünler hariç
                if item_price < (current_price * 0.30): 
                    continue

            # B) KELİME ZORUNLULUĞU
            # Aranan ana marka ve model ismi (Örn: Samsung Tab A11) başlıkta yoksa ele.
            required_keywords = words[:3] 
            if not all(k.lower() in item_title for k in required_keywords):
                continue

            # C) YASAKLI KATEGORİ TEMİZLİĞİ
            # Eğer ana ürün "kitap" değilse ama sonuçta kitap kelimeleri geçiyorsa ele.
            book_words = ["kitap", "roman", "dergi", "kılıf", "ekran koruyucu", "yedek parça"]
            if any(bw in item_title for bw in book_words) and not any(bw in original_title for bw in book_words):
                continue

            final_list.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": actual_link,
                "image": item.get("thumbnail"),
                "raw_price": item_price
            })
        
        # Fiyatları sırala (Gerçek rakipler arasında en ucuzu bul)
        final_list.sort(key=lambda x: x['raw_price'])
        
        return jsonify({"results": final_list[:10]})
        
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

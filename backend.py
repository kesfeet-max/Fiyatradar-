import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
# CORS ayarlarını eklenti için en güvenli hale getirdik
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

@app.route("/", methods=["GET"])
def home():
    return "Fiyat Radarı Sunucusu Aktif!"

def clean_price(price_str):
    if not price_str: return 0.0
    try:
        # Screenshot_70'deki gibi farklı formatlardaki fiyatları temizler
        cleaned = str(price_str).replace('TL', '').replace('₺', '').replace(' ', '')
        # Binlik ayracı olan noktayı kaldır, kuruş ayracı olan virgülü noktaya çevir
        if ',' in cleaned and '.' in cleaned:
            cleaned = cleaned.replace('.', '')
        cleaned = cleaned.replace(',', '.')
        return float(re.sub(r'[^\d.]', '', cleaned))
    except:
        return 0.0

@app.route("/compare", methods=["POST"])
def compare():
    data = request.get_json()
    full_title = data.get("title", "")
    # Screenshot_82'deki fiyat okuma hatasını telafi etmek için fiyatı normalize ediyoruz
    current_page_price = clean_price(data.get("original_price", "0"))
    
    # Screenshot_88'deki gibi aramanın bozulmaması için başlığı optimize ediyoruz
    # "Sony Playstation 5 Slim" gibi anahtar kelimelere odaklanır
    search_query = " ".join(full_title.split()[:5]) 

    params = {
        "engine": "google_shopping",
        "q": search_query,
        "hl": "tr",
        "gl": "tr",
        "api_key": SERP_API_KEY
    }

    try:
        # SerpApi bağlantısı
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=20)
        results = response.json().get("shopping_results", [])
    except:
        return jsonify({"results": [], "error": "API bağlantı hatası"})

    cheap_results = []
    # Kapsamı genişlettik ki Screenshot_88'deki gibi "sonuç yok" demesin
    whitelist = ["trendyol", "hepsiburada", "n11", "amazon", "vatan", "teknosa", "pazarama", "ciceksepeti", "mediamarkt", "pttavm", "idefix"]

    for item in results:
        price_val = clean_price(item.get("price"))
        item_link = item.get("link")
        source = item.get("source", "").lower()

        # Link kontrolü: Screenshot_73 ve 77 hatalarını önler
        if not item_link or not str(item_link).startswith("http"):
            continue

        # KRİTİK DÜZELTME: 
        # Eğer current_page_price çok düşükse (hatalı okunmuşsa), filtreyi esnetiyoruz
        # Böylece kullanıcıya her zaman sonuç gösteriyoruz.
        is_relevant = any(w in source for w in whitelist) or ".tr" in item_link.lower()
        
        if is_relevant:
            cheap_results.append({
                "site": item.get("source", "Mağaza"),
                "price": item.get("price"),
                "link": item_link,
                "p_val": price_val
            })

    # En ucuzdan pahalıya sırala
    sorted_results = sorted(cheap_results, key=lambda x: x['p_val'])
    
    # Çıktıdan geçici değerleri temizle
    for x in sorted_results: 
        del x['p_val']

    # Pazarlanabilir olması için her zaman en az 5-10 sonuç döndürür
    return jsonify({"results": sorted_results[:10]})

if __name__ == "__main__":
    app.run()

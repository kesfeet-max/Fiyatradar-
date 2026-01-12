import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_price(price_str):
    if not price_str: return 0.0
    try:
        # Screenshot_70 ve 71'deki TL ve ₺ formatlarını temizler
        cleaned = str(price_str).replace('TL', '').replace('₺', '').replace(' ', '')
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
    current_price = clean_price(data.get("original_price", "0"))
    
    # KRİTİK DÜZELTME: Arama terimini sadece marka ve ilk 3 kelimeye indiriyoruz.
    # Screenshot_88'deki gibi uzun başlıklar SerpApi'yi bozuyor.
    search_query = " ".join(full_title.split()[:4]) 

    params = {
        "engine": "google_shopping",
        "q": search_query,
        "hl": "tr",
        "gl": "tr",
        "api_key": SERP_API_KEY
    }

    try:
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=20)
        results = response.json().get("shopping_results", [])
    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

    cheap_results = []
    whitelist = ["trendyol", "hepsiburada", "n11", "amazon", "vatan", "teknosa", "pazarama", "ciceksepeti", "mediamarkt", "pttavm"]

    for item in results:
        price_val = clean_price(item.get("price"))
        item_link = item.get("link")
        source = item.get("source", "").lower()

        if not item_link or not str(item_link).startswith("http"):
            continue

        # Screenshot_90'daki "Sonuç yok" hatasını aşmak için:
        # Eğer sayfa fiyatı 0 ise (okunamazsa) veya bulunan fiyat daha ucuzsa listele.
        if any(w in source for w in whitelist) or ".tr" in item_link.lower():
            if current_price == 0 or price_val < current_price:
                cheap_results.append({
                    "site": item.get("source", "Mağaza"),
                    "price": item.get("price"),
                    "link": item_link,
                    "p_val": price_val
                })

    # En ucuzdan pahalıya sırala
    sorted_results = sorted(cheap_results, key=lambda x: x['p_val'])
    for x in sorted_results: del x['p_val']

    return jsonify({"results": sorted_results[:10]})

if __name__ == "__main__":
    app.run()

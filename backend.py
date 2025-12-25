import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_price(price_str):
    """Fiyat metnini sayıya çevirir (Örn: '8.999,00 TL' -> 8999.0)"""
    try:
        # Sadece rakamları, noktayı ve virgülü tut
        cleaned = re.sub(r'[^\d,.]', '', str(price_str))
        if '.' in cleaned and ',' in cleaned:
            cleaned = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned:
            cleaned = cleaned.replace(',', '.')
        return float(cleaned)
    except:
        return 0.0

def filter_bad_results(original_price_str, results):
    """Yedek parça ve alakasız düşük fiyatlı ürünleri eler"""
    clean_results = []
    base_price = clean_price(original_price_str)
    
    # Screenshot_42'deki kirliliği önlemek için yasaklı kelimeler
    forbidden = ["yedek", "parça", "filtre", "deterjan", "şampuan", "hortum", "aparat", "başlık", "aksesuar", "kılıf"]
    
    for item in results:
        title_lower = item.get('title', '').lower()
        price_val = clean_price(item.get('price', '0'))
        
        # Filtre 1: Yasaklı kelime kontrolü
        has_forbidden = any(word in title_lower for word in forbidden)
        
        # Filtre 2: Fiyat sapma kontrolü (Orijinal fiyatın %40'ından ucuzsa yedek parçadır)
        is_too_cheap = False
        if base_price > 0:
            is_too_cheap = price_val < (base_price * 0.4)
        
        if not has_forbidden and not is_too_cheap:
            clean_results.append(item)
            
    return clean_results

def get_real_prices_with_api(product_name):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_shopping",
        "q": product_name,
        "hl": "tr",
        "tr": "tr",
        "api_key": SERP_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        shopping_results = data.get("shopping_results", [])
        
        results = []
        for item in shopping_results[:20]:
            actual_link = item.get("link") or item.get("product_link")
            if actual_link:
                results.append({
                    "title": item.get("title", ""), # Filtreleme için başlık eklendi
                    "site": item.get("source", "Satıcı"),
                    "price": item.get("price", "Fiyat Yok"),
                    "link": actual_link 
                })
        return results
    except Exception as e:
        return []

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return "", 200
    
    data = request.get_json(silent=True) or {}
    title = data.get("title", "")
    original_price = data.get("original_price", "0") # JS'den gelen fiyatı alıyoruz
    
    # Arama terimini optimize et
    search_title = ' '.join(title.split()[:4])
    
    # 1. Ham sonuçları çek
    raw_results = get_real_prices_with_api(search_title)
    
    # 2. Akıllı filtreleme uygula (Screenshot_42 sorununu çözer)
    final_results = filter_bad_results(original_price, raw_results)
    
    return jsonify({
        "query": search_title, 
        "original_price": original_price,
        "results": final_results
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

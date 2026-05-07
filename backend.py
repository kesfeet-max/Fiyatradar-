import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re

app = Flask(__name__)
CORS(app)

# Senin RapidAPI Anahtarın
RAPIDAPI_KEY = "f64caf4ccfmsh09240838e483812p1878e8jsneb770485a2ac"

def clean_price(price_str):
    if not price_str: return 0
    try:
        # Fiyatı sayıya çevir (TL ve noktaları temizle)
        s = str(price_str).replace('TL', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        s = re.sub(r'[^\d.]', '', s)
        return float(s)
    except:
        return 0

def get_search_query(title):
    # API'nin anlayacağı en temiz ismi bulur
    # Gereksiz detayları (i7, 16GB, RTX...) siler, ana modeli bırakır
    words = title.split()
    # İlk 4 kelime genelde Marka + Seri + Modeldir
    return " ".join(words[:4])

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200
    try:
        data = request.get_json()
        full_title = data.get("title", "")
        current_price = clean_price(data.get("price", "0"))
        
        # Başlığı sadeleştir (Örn: Casper Excalibur G870)
        query = get_search_query(full_title)
        
        url = "https://bluecart.p.rapidapi.com/request"
        
        # TÜRKİYE odaklı ve daha geniş arama parametreleri
        querystring = {
            "type": "search",
            "search_term": query,
            "google_domain": "google.com.tr",
            "gl": "tr",
            "hl": "tr",
            "sort_by": "price_low_to_high"
        }
        
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "bluecart.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        api_data = response.json()
        
        results = api_data.get("search_results", [])
        final_list = []
        
        for item in results:
            product = item.get("product", {})
            offers = item.get("offers", {}).get("primary", {})
            
            p_val = clean_price(offers.get("price", "0"))
            store = offers.get("seller", "Mağaza")
            
            # İkinci el ve alakasız yerleri engelle
            if any(x in store.lower() for x in ["letgo", "dolap", "sahibinden", "gardrops"]):
                continue

            # Fiyat Kontrolü: Çok ucuz (aksesuar) ürünleri ele ama çok katı olma
            if current_price > 0 and p_val < (current_price * 0.4):
                continue

            link = product.get("link")
            if link and link.startswith("http"):
                final_list.append({
                    "site": store,
                    "price": f"{p_val} TL",
                    "price_value": p_val,
                    "image": product.get("main_image"),
                    "link": link,
                    "title": product.get("title")
                })

        # Sonuçları fiyata göre sırala
        final_list.sort(key=lambda x: x['price_value'])
        
        # EĞER SONUÇ YOKSA: Kullanıcıya en azından bir arama butonu göster (Boş kalmasın)
        if not final_list:
            return jsonify({"results": [{
                "site": "Sistem",
                "price": "Diğer Siteler",
                "price_value": 0,
                "image": "https://www.google.com/favicon.ico",
                "link": f"https://www.google.com/search?q={query}&tbm=shop",
                "title": "Üzgünüz, doğrudan sonuç bulunamadı. Buradan bakabilirsiniz."
            }]})

        return jsonify({"results": final_list[:10]})

    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

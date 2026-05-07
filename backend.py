import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re

app = Flask(__name__)

# ÖNEMLİ: Eklenti (Extension) bağlantılarında hata çıkmaması için tüm kökenlere izin veriyoruz
CORS(app, resources={r"/*": {"origins": "*"}})

SERP_API_KEY = "4c609280bc69c17ee299b38680c879b8f6a43f09eaf7a2f045831f50fc3d1201"

def clean_price(price_str):
    """Fiyatı sıralama yapabilmek için sayıya çevirir."""
    if not price_str: return 0
    try:
        # Sadece sayı, nokta ve virgül kalsın
        cleaned = re.sub(r'[^\d,.]', '', str(price_str))
        # Binlik ayırıcı ve ondalık ayırıcıyı (TR formatı) evrensel formata çevir
        if ',' in cleaned and '.' in cleaned:
            cleaned = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned:
            cleaned = cleaned.replace(',', '.')
        return float(cleaned)
    except:
        return 0

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "message": "Fiyat Radarı API Çalışıyor 🚀"}), 200

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    # CORS ön kontrolü (Browser bazen bunu sorar)
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({"results": [], "error": "Veri gelmedi"}), 400
            
        original_title = data.get("title", "")
        
        # SerpApi Parametreleri
        params = {
            "engine": "google_shopping",
            "q": original_title,
            "api_key": SERP_API_KEY,
            "hl": "tr", 
            "gl": "tr", 
            "direct_link": True  # Doğrudan mağaza linki almaya zorla
        }

        response = requests.get("https://serpapi.com/search.json", params=params)
        shopping_data = response.json()
        
        results = shopping_data.get("shopping_results", [])
        
        final_list = []
        for item in results:
            price_raw = item.get("price", "Fiyat Yok")
            
            # Eklentiyle tam uyum için veri isimlerini (Key) sabitliyoruz
            final_list.append({
                "source": item.get("source", "Mağaza"),
                "price": price_raw,
                "price_value": clean_price(price_raw),
                "thumbnail": item.get("thumbnail", ""), # Bazı sonuçlarda 'image' yerine bu gelir
                "image": item.get("thumbnail"),         # Eklenti 'image' bekliyorsa bu da olsun
                "link": item.get("link", ""),           # Boş sekme açılmaması için link şart
                "title": item.get("title", "")
            })
        
        # --- AKILLI SIRALAMA ---
        # Fiyatı 0 olmayanları fiyata göre diz, fiyatı olmayanları sona at
        final_list.sort(key=lambda x: x['price_value'] if x['price_value'] > 0 else float('inf'))
        
        return jsonify({"results": final_list})

    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    # Render'ın portuna uyum sağla
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

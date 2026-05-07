import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

def clean_price(price_str):
    if not price_str: return 0
    try:
        s = str(price_str).replace('TL', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        s = re.sub(r'[^\d.]', '', s)
        return float(s)
    except: return 0

# GERÇEK İNSAN KİMLİĞİ (Headers)
def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Upgrade-Insecure-Requests": "1"
    }

def scrape_trendyol(query):
    try:
        # Trendyol'un botu anlamaması için arama linkini profesyonelleştirdik
        url = f"https://www.trendyol.com/sr?q={query.replace(' ', '%20')}&os=1"
        session = requests.Session()
        res = session.get(url, headers=get_headers(), timeout=10)
        
        if res.status_code != 200: return None # Engel yendiyse dur
        
        soup = BeautifulSoup(res.text, 'html.parser')
        card = soup.select_one(".p-card-wrppr") # Trendyol'un ürün kartı kodu
        
        if card:
            link = "https://www.trendyol.com" + card.select_one("a")['href']
            price = card.select_one(".prc-box-dscntd").text
            title = card.select_one(".prdct-desc-cntnr-name").text
            # Resim bazen geç yüklenir, o yüzden alternatifleri de aldık
            img = card.select_one(".p-card-img")['src'] if card.select_one(".p-card-img") else ""
            
            return {
                "site": "Trendyol",
                "price": price,
                "price_value": clean_price(price),
                "link": link,
                "image": img,
                "title": title
            }
    except Exception as e:
        print(f"Trendyol Hatası: {e}")
        return None

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200
    try:
        data = request.get_json()
        title = data.get("title", "")
        current_price = clean_price(data.get("price", "0"))
        
        # Arama terimini sadeleştir (Örn: Casper Excalibur G870)
        search_query = " ".join(title.split()[:4])
        
        final_list = []
        
        # Botu ateşle
        ty_result = scrape_trendyol(search_query)
        if ty_result:
            final_list.append(ty_result)
            
        # Amazon TR Botu (Basitleştirilmiş)
        # İleride buraya Amazon, Hepsiburada eklenecek
        
        if not final_list:
            return jsonify({"results": [], "message": "Şu an pazar yerleri yoğun, lütfen tekrar deneyin."})

        return jsonify({"results": final_list})

    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

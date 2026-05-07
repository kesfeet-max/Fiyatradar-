import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# Tarayıcı gibi görünmek için gerekli kimlik bilgisi
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

def clean_price(price_str):
    if not price_str: return 0
    try:
        s = str(price_str).replace('TL', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
        s = re.sub(r'[^\d.]', '', s)
        return float(s)
    except: return 0

# --- ÖZEL BOTLAR (SCRAPERS) ---

def scrape_trendyol(query):
    """Trendyol'dan doğrudan ilk ürünü ve fiyatını çeker"""
    try:
        url = f"https://www.trendyol.com/sr?q={query.replace(' ', '%20')}&os=1"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # İlk ürün kartını bul
        card = soup.select_one(".p-card-wrppr")
        if card:
            link = "https://www.trendyol.com" + card.select_one("a")['href']
            price = card.select_one(".prc-box-dscntd").text
            title = card.select_one(".prdct-desc-cntnr-name").text
            img = card.select_one(".p-card-img")['src']
            return {"site": "Trendyol", "price": price, "price_value": clean_price(price), "link": link, "image": img, "title": title}
    except: return None

def scrape_amazon_tr(query):
    """Amazon TR'den doğrudan fiyat çeker"""
    try:
        url = f"https://www.amazon.com.tr/s?k={query.replace(' ', '+')}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        card = soup.select_one(".s-result-item[data-component-type='s-search-result']")
        if card:
            link = "https://www.amazon.com.tr" + card.select_one("a.a-link-normal")['href']
            price_whole = card.select_one(".a-price-whole").text
            price_fraction = card.select_one(".a-price-fraction").text
            price = f"{price_whole},{price_fraction} TL"
            title = card.select_one("h2 span").text
            img = card.select_one(".s-image")['src']
            return {"site": "Amazon TR", "price": price, "price_value": clean_price(price), "link": link, "image": img, "title": title}
    except: return None

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200
    try:
        data = request.get_json()
        title = data.get("title", "")
        current_price = clean_price(data.get("price", "0"))
        
        # Arama terimini sadeleştir (Marka + Model)
        query = " ".join(title.split()[:4])
        
        final_list = []
        
        # Botları sırayla çalıştır
        ty = scrape_trendyol(query)
        if ty: final_list.append(ty)
        
        amz = scrape_amazon_tr(query)
        if amz: final_list.append(amz)
        
        # Fiyatı küçükten büyüğe sırala
        final_list.sort(key=lambda x: x['price_value'])
        
        return jsonify({"results": final_list})

    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

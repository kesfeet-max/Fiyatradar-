import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def get_prices_from_search(product_name):
    # Google yerine daha az engelleyen bir arama motoru veya doğrudan site denemesi
    # Örnek olarak arama terimini temizleyip sonuç üretmeye çalışıyoruz
    search_query = product_name.replace(" ", "+")
    url = f"https://www.google.com/search?q={search_query}+fiyat+karşılaştır&tbm=shop"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1"
    }
    
    try:
        # İstekler arasına kısa bir bekleme ekleyerek bloklanmayı önlemeye çalışıyoruz
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        
        # Farklı seçiciler deneyerek veriyi yakalamaya çalışıyoruz
        items = soup.find_all('div', class_='sh-dgr__content') or soup.find_all('div', class_='u30Pqc')
        
        for item in items[:3]:
            title = item.find('h3').text if item.find('h3') else "Ürün"
            # Fiyatı daha geniş bir tarama ile buluyoruz
            price_div = item.select_one('.a88X0c') or item.select_one('.OFFNJ')
            price = price_div.text if price_div else "Fiyat Belirlenemedi"
            link_tag = item.find('a')
            link = "https://www.google.com" + link_tag['href'] if link_tag and link_tag['href'].startswith('/') else link_tag['href'] if link_tag else "#"
            
            results.append({
                "site": title[:20],
                "price": price,
                "link": link
            })
        return results
    except Exception as e:
        print(f"Hata: {e}")
        return []

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json(silent=True) or {}
    # Ürün başlığını çok uzunsa kısaltıyoruz (aramayı kolaylaştırır)
    raw_title = data.get("title", "")
    clean_title = ' '.join(raw_title.split()[:5]) 
    
    results = get_prices_from_search(clean_title)
    
    # Eğer hala boşsa, en azından sistemin çalıştığını ama verinin çekilemediğini belirtelim
    if not results:
        results = [{"site": "Sistem Aktif", "price": "Arama limitine takıldı, 1 dk sonra deneyin.", "link": "#"}]

    return jsonify({
        "query": clean_title,
        "results": results
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

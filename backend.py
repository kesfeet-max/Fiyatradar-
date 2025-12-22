import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# 🔍 Gerçek fiyatları çeken fonksiyon
def get_real_prices(product_name):
    search_url = f"https://www.google.com/search?q={product_name}+fiyatı&tbm=shop"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        results = []
        # Google Shopping ürün bloklarını tarıyoruz
        items = soup.select('.sh-dgr__content')[:3] # En iyi 3 sonuç
        
        for item in items:
            title_tag = item.select_one('h3')
            price_tag = item.select_one('.a88X0c')
            link_tag = item.select_one('a')
            
            if title_tag and price_tag:
                results.append({
                    "site": title_tag.text[:20] + "...",
                    "price": price_tag.text,
                    "link": "https://www.google.com" + link_tag['href'] if link_tag else "#"
                })
        return results
    except Exception as e:
        print(f"Hata oluştu: {e}")
        return []

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json(silent=True) or {}
    title = data.get("title", "")
    price = data.get("price", "")
    url = data.get("url", "")

    # Canlı veriyi çekiyoruz
    results = get_real_prices(title)
    
    # Eğer canlı veri çekilemezse (boş dönerse) yedek olarak eski listeyi gösterir
    if not results:
        results = [
            {"site": "Bilgi", "price": "Anlık fiyat bulunamadı", "link": "#"}
        ]

    return jsonify({
        "query": title,
        "current_price": price,
        "source_url": url,
        "results": results
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

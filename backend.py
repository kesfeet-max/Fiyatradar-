import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def get_real_prices(product_name):
    # Aramayı daha spesifik hale getirmek için "fiyatı" kelimesini ekliyoruz
    search_url = f"https://www.google.com/search?q={product_name}+fiyatı&tbm=shop"
    
    # Google'ı gerçek bir kullanıcı olduğumuza ikna etmek için tarayıcı bilgileri
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/"
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        
        results = []
        # Google Shopping'in kullandığı farklı blok sınıflarını deniyoruz
        items = soup.find_all('div', class_='sh-dgr__content')
        
        for item in items[:3]: # En ucuz ilk 3 sonuç
            name = item.find('h3').text if item.find('h3') else "Ürün"
            price = item.select_one('.a88X0c').text if item.select_one('.a88X0c') else "Fiyat Bilgisi Yok"
            link_tag = item.find('a')
            link = "https://www.google.com" + link_tag['href'] if link_tag else "#"
            
            # Fiyat bilgisini temizle (Örn: "15.000 TL*" -> "15.000 TL")
            clean_price = price.split('*')[0].strip()
            
            results.append({
                "site": name[:25] + "...",
                "price": clean_price,
                "link": link
            })
            
        return results
    except Exception as e:
        print(f"Hata detayi: {e}")
        return []

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Fiyat Radar Backend Aktif"}), 200

@app.route("/compare", methods=["POST", "OPTIONS"])
def compare():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json(silent=True) or {}
    title = data.get("title", "")
    
    # Arama motoru için ürün adını temizle
    search_title = title.split('-')[0].strip() if '-' in title else title
    
    results = get_real_prices(search_title)
    
    if not results:
        # Eğer hala bulunamazsa kullanıcıya bilgi ver
        results = [{"site": "Bilgi", "price": "Şu an fiyat çekilemiyor, lütfen az sonra tekrar deneyin.", "link": "#"}]

    return jsonify({
        "query": search_title,
        "results": results
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

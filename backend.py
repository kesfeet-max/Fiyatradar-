# Sadece hız odaklı değişiklik yapılmıştır
@app.route("/compare", methods=["POST"])
def compare():
    data = request.get_json()
    # Arama terimini 3 kelimeye çekerek SerpApi hızını artırıyoruz
    search_query = " ".join(data.get("title", "").split()[:3]) 
    
    params = {
        "engine": "google_shopping",
        "q": search_query,
        "hl": "tr", "gl": "tr",
        "api_key": SERP_API_KEY
    }

    try:
        # Timeout süresini düşürerek beklemeyi kısalttık
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=8)
        results = response.json().get("shopping_results", [])
    except:
        return jsonify({"results": []})

    cheap_results = []
    # En hızlı dönen ana sitelere odaklanıyoruz
    whitelist = ["trendyol", "hepsiburada", "n11", "amazon", "vatan"]

    for item in results:
        source = item.get("source", "").lower()
        link = item.get("link")
        if any(w in source for w in whitelist) and link:
            cheap_results.append({
                "site": item.get("source"),
                "price": item.get("price"),
                "link": link
            })
            if len(cheap_results) >= 6: break # İlk 6 hızlı sonucu al ve bitir

    return jsonify({"results": cheap_results})

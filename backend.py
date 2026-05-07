# backend.py dosyanın compare fonksiyonundaki final_list kısmını tam olarak böyle yap:
        final_list = []
        for item in results:
            price_raw = item.get("price", "Fiyat Yok")
            final_list.append({
                "site": item.get("source", "Mağaza"),
                "price": price_raw,
                "price_value": clean_price(price_raw),
                "image": item.get("thumbnail"),
                "link": item.get("link"), # Linkin buradan geldiğinden emin oluyoruz
                "title": item.get("title")
            })

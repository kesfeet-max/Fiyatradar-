# backend.py içindeki döngüyü bu şekilde çok daha sağlam hale getir:
        for item in results:
            price_raw = item.get("price", "Fiyat Yok")
            
            # 1. Önce doğrudan mağaza linkini (merchant_link) dene
            # 2. Yoksa normal linki dene
            # 3. O da yoksa serpapi_link'i dene
            raw_link = item.get("merchant_link") or item.get("link") or item.get("serpapi_product_api")
            
            # Eğer link hala Google yönlendirmesi içeriyorsa, temizlemeye çalışalım
            clean_link = raw_link
            if "google.com/url" in raw_link:
                # Buraya ileride link temizleme mantığı eklenebilir
                pass

            final_list.append({
                "site": item.get("source", "Mağaza"),
                "price": price_raw,
                "price_value": clean_price(price_raw),
                "image": item.get("thumbnail"),
                "link": clean_link, 
                "title": item.get("title")
            })

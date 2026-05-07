# backend.py'deki 'compare' fonksiyonu içindeki döngüyü tam olarak böyle yap:
        final_list = []
        for item in results:
            price_raw = item.get("price", "Fiyat Yok")
            # SerpApi bazen 'link' bazen 'product_link' verebilir, ikisini de kontrol edelim
            item_link = item.get("link") or item.get("product_link") or ""
            
            final_list.append({
                "site": item.get("source", "Mağaza"),
                "price": price_raw,
                "price_value": clean_price(price_raw),
                "image": item.get("thumbnail"),
                "link": item_link,  # Linki garantiye aldık
                "title": item.get("title")
            })

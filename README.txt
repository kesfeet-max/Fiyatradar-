FiyatRadar MVP - İçerik
=======================

Bu paket şu dosyaları içerir:
- manifest.json
- content_script.js
- background.js
- popup.html
- popup.js
- icons/*.png
- backend.py (basit Flask örneği)

Nasıl çalışır?
1) Chrome'da extension olarak yükle:
   - chrome://extensions -> Geliştirici modu -> "Paketlenmemiş uzantı yükle" -> bu klasörü seçin
2) Backend'i çalıştırın:
   - Python 3.10+ ile
   - pip install flask
   - python backend.py
3) Bir ürün sayfasında extension popup'ını açın ve "Fiyatları Karşılaştır" butonuna basın.
   - Popup backend'e POST isteği gönderir, backend mock sonuç döner.
4) Gerçek veri için:
   - Trendyol, Hepsiburada, Amazon affiliate API'lerine kayıt olun ve backend'i bu API'ler ile entegre edin.
   - Alternatif: yasal scraping (robots.txt ve site kullanım şartlarına uygun olarak).
   - Affiliate linkleri backend'de dönüştürerek kullanıcıya gösterin.

Geliştirme Notları / İleri Adımlar:
- Veri kaynağı olarak önce affiliate API'lerini kullanmanız en güvenli ve güvenilir yoldur.
- Ürün eşleştirme için fuzzy matching (fuzzywuzzy) ve başlık/UPC/ISBN gibi benzersiz alanlar kullanın.
- Fiyat geçmişi için bir zaman serisi database (timescaledb veya basit bir Postgres) kurun.
- Kullanıcı bildirimleri için Firebase Cloud Messaging veya Push API entegrasyonu yapın.
- Chrome Web Store için manifest, gizlilik politikası ve web sitesinde açık bilgiler gereklidir.

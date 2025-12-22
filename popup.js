async function getProductFromPage() {
  const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
  try {
    const resp = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        return window.__fiyatradar_product || {title:'', price:'', url:location.href};
      },
    });
    return resp?.[0]?.result || {title:'', price:'', url: ''};
  } catch (e) {
    return {title: 'Ürün bilgisi alınamadı', price: '', url: ''};
  }
}

function renderProduct(p) {
  const d = document.getElementById('product');
  if (!p || (!p.title && !p.price)) {
    d.innerHTML = '<div class="row">Ürün sayfası açık değil.</div>';
    return;
  }
  d.innerHTML = `
    <div class="row"><strong>Başlık:</strong> ${p.title || '(bulunamadı)'}</div>
    <div class="row"><strong>Fiyat (sayfada):</strong> ${p.price || '(yok)'}</div>
    <div class="row"><strong>URL:</strong> <small style="word-break: break-all;">${p.url}</small></div>
  `;
}

function renderResults(list) {
  const r = document.getElementById('results');
  if (!list || list.length === 0) { 
    r.innerText = 'Sonuç bulunamadı.'; 
    return; 
  }
  r.innerHTML = '';
  list.forEach(item => {
    const div = document.createElement('div');
    div.className = "result-row";
    // Linkin tıklanabilir olması için target="_blank" ve href eklendi
    div.innerHTML = `
      <div style="margin-bottom: 5px;">
        <strong>${item.site}</strong>: ${item.price} 
        <a href="${item.link}" target="_blank" style="color: blue; font-weight: bold; margin-left: 10px;">— Git</a>
      </div>
    `;
    r.appendChild(div);
  });
}

document.getElementById('compare').addEventListener('click', async () => {
  const r = document.getElementById('results');
  r.innerText = 'Fiyatlar araştırılıyor, lütfen bekleyin...';
  
  const product = await getProductFromPage();
  renderProduct(product);

  if (!product.title) {
    r.innerText = 'Hata: Ürün adı tespit edilemedi.';
    return;
  }

  try {
    // URL düzeltildi
    const API_URL = "https://fiyatradar-3mcl.onrender.com/compare";
    
    const resp = await fetch(API_URL, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        title: product.title, 
        url: product.url,
        price: product.price
      })
    });

    if (!resp.ok) throw new Error('Sunucu yanıt vermedi.');

    const j = await resp.json();
    renderResults(j.results);
  } catch (e) {
    r.innerText = 'Bağlantı Hatası: ' + e.message;
  }
});

// Eklenti açıldığında ürün bilgilerini getir
getProductFromPage().then(p => renderProduct(p));

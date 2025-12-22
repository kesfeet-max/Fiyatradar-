async function getProductFromPage() {
  // Ask content script for stored product
  const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
  const resp = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => {
      return window.__fiyatradar_product || {title:'', price:'', url:location.href};
    },
  });
  return resp?.[0]?.result || {title:'', price:'', url: location.href};
}

function renderProduct(p) {
  const d = document.getElementById('product');
  d.innerHTML = '<div class="row"><strong>Başlık:</strong> ' + (p.title || '(bulunamadı)') + '</div>'
              + '<div class="row"><strong>Fiyat (sayfada):</strong> ' + (p.price || '(yok)') + '</div>'
              + '<div class="row"><strong>URL:</strong> <small>' + p.url + '</small></div>';
}

function renderResults(list) {
  const r = document.getElementById('results');
  if (!list || list.length===0) { r.innerText = 'Sonuç yok'; return; }
  r.innerHTML = '';
  list.forEach(item => {
    const div = document.createElement('div');
    div.innerHTML = '<div class="row"><span class="site">'+item.site+'</span>: ' + item.price + ' — <a href="'+item.link+'" target="_blank">Git</a></div>';
    r.appendChild(div);
  });
}

document.getElementById('compare').addEventListener('click', async () => {
  document.getElementById('results').innerText = 'Karşılaştırılıyor...';
  const product = await getProductFromPage();
  renderProduct(product);
  try {
    // Call backend (you must run backend and set correct URL)
    const resp = await fetch('const API_URL = "https://fiyatradar-3mcl.onrender.com/compare";', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({title: product.title, url: product.url})
    });
    const j = await resp.json();
    renderResults(j.results);
  } catch (e) {
    document.getElementById('results').innerText = 'Backend çalışmıyor veya CORS hatası: ' + e.message;
  }
});

// on open, fetch product
getProductFromPage().then(p => renderProduct(p));

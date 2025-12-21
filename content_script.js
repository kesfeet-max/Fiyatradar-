(function(){
  // Try to extract common product fields
  function extract() {
    const title = document.querySelector('meta[property="og:title"]')?.content ||
                  document.querySelector('title')?.innerText || '';
    // Try common price selectors (may vary by site)
    let price = '';
    const priceSelectors = ['.price', '.product-price', '[itemprop="price"]', '.prc'];
    for (const sel of priceSelectors) {
      const el = document.querySelector(sel);
      if (el) { price = el.innerText.trim(); break; }
    }
    return { title, price, url: location.href };
  }

  // Store on window for popup to access
  window.__fiyatradar_product = extract();

  // Observe changes for single-page apps (optional)
  const ro = new MutationObserver(() => {
    window.__fiyatradar_product = extract();
  });
  ro.observe(document.body, { childList: true, subtree: true });
})();

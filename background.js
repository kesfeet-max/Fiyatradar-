chrome.runtime.onInstalled.addListener(() => {
  console.log('FiyatRadar installed');
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'FETCH_PRODUCT') {
    // forward to popup or handle if needed
    sendResponse({status: 'ok', product: msg.product});
  }
});

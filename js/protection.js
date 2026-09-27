/**
 * Anti-Crawling & Content Protection System (Daily Korean Shield)
 * Multi-layer client-side security against scrapers and data theft.
 */

(function initProtection() {
  // 1. Disable Right Click (Context Menu)
  document.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    showProtectionAlert("우클릭 방지: 이미지 및 본문 불법 복제가 금지되어 있습니다. / Right click disabled.");
    return false;
  });

  // 2. Disable Text Selection & Dragging
  document.addEventListener('selectstart', (e) => {
    if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
      e.preventDefault();
      return false;
    }
  });

  document.addEventListener('dragstart', (e) => {
    e.preventDefault();
    return false;
  });

  // 3. Block Developer Tools & Copy Shortcuts
  document.addEventListener('keydown', (e) => {
    const isCtrlOrCmd = e.ctrlKey || e.metaKey;

    // F12 key
    if (e.key === 'F12' || e.keyCode === 123) {
      e.preventDefault();
      showProtectionAlert("개발자 도구(F12) 접근이 제한되었습니다. / DevTools disabled.");
      return false;
    }

    if (isCtrlOrCmd) {
      // Ctrl+Shift+I (DevTools), Ctrl+Shift+J (Console), Ctrl+Shift+C (Inspect)
      if (e.shiftKey && ['I', 'J', 'C', 'i', 'j', 'c'].includes(e.key)) {
        e.preventDefault();
        showProtectionAlert("개발자 단축키 사용이 금지되었습니다. / DevTools shortcut disabled.");
        return false;
      }
      // Ctrl+U (View Source)
      if (['u', 'U'].includes(e.key)) {
        e.preventDefault();
        showProtectionAlert("소스 보기(Ctrl+U)가 금지되었습니다. / View Source disabled.");
        return false;
      }
      // Ctrl+S (Save Page)
      if (['s', 'S'].includes(e.key)) {
        e.preventDefault();
        showProtectionAlert("페이지 저장(Ctrl+S)이 금지되었습니다. / Page saving disabled.");
        return false;
      }
      // Ctrl+C (Copy)
      if (['c', 'C'].includes(e.key) && window.getSelection().toString().length > 0) {
        e.preventDefault();
        showProtectionAlert("무단 텍스트 복사(Ctrl+C)가 제한되어 있습니다. / Copying text disabled.");
        return false;
      }
      // Ctrl+P (Print)
      if (['p', 'P'].includes(e.key)) {
        e.preventDefault();
        showProtectionAlert("인쇄(Ctrl+P)가 제한되어 있습니다. / Printing disabled.");
        return false;
      }
    }
  });

  // 4. DevTools Detector
  let devtoolsOpen = false;
  const element = new Image();
  Object.defineProperty(element, 'id', {
    get: function () {
      devtoolsOpen = true;
      showDevToolsWarning();
    }
  });

  setInterval(function () {
    devtoolsOpen = false;
    console.log('%c', element);
    console.clear();
  }, 2000);

  function showProtectionAlert(msg) {
    let toast = document.getElementById('daily-korean-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'daily-korean-toast';
      toast.style.cssText = `
        position: fixed;
        bottom: 24px;
        left: 50%;
        transform: translateX(-50%);
        background: #111827;
        color: #f3f4f6;
        padding: 12px 24px;
        border-radius: 9999px;
        font-size: 14px;
        font-weight: 600;
        z-index: 999999;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        border: 1px solid #374151;
        transition: opacity 0.3s ease;
      `;
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.style.opacity = '1';
    clearTimeout(window.toastTimer);
    window.toastTimer = setTimeout(() => {
      toast.style.opacity = '0';
    }, 2500);
  }

  function showDevToolsWarning() {
    console.warn("⚠️ Daily Korean Protection: Developer tools detected!");
  }
})();

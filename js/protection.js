/**
 * Daily Korean News Security Layer
 * 1. Honeypot Fake Input Trap
 * 2. Client-Side Security Signature Generation
 * 3. Asynchronous Data Fetching Engine (Lazy/Async Content Loading)
 */

window.DailyKoreanShield = (function () {
  // 1. Generate Security Session Token
  const sessionToken = "dk_sig_" + Math.random().toString(36).substring(2, 15) + "_" + Date.now();
  sessionStorage.setItem('DK_SESSION_TOKEN', sessionToken);

  let isBotDetected = false;

  // 2. Honeypot Input Verification Listener
  document.addEventListener('DOMContentLoaded', () => {
    const hpInput = document.getElementById('hp_trap_field');
    if (hpInput) {
      hpInput.addEventListener('change', () => {
        if (hpInput.value.trim() !== '') {
          isBotDetected = true;
          console.warn("⚠️ Bot activity flagged by Honeypot input!");
        }
      });
    }
  });

  // 3. Secure Async Data Loading Function
  async function loadLessonData() {
    // Honeypot check
    const hpInput = document.getElementById('hp_trap_field');
    if ((hpInput && hpInput.value !== '') || isBotDetected) {
      throw new Error("Access denied by Security Shield.");
    }

    // Verify session token
    const token = sessionStorage.getItem('DK_SESSION_TOKEN');
    if (!token) {
      throw new Error("Invalid session verification token.");
    }

    // Perform Async Fetch request with custom verification headers
    const response = await fetch(`data/lessons.json?v=${Date.now()}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'X-Daily-Korean-Signature': token,
        'X-Requested-With': 'XMLHttpRequest'
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to load lessons data: ${response.status}`);
    }

    const data = await response.json();
    return data.featured;
  }

  return {
    loadLessonData,
    getToken: () => sessionToken
  };
})();

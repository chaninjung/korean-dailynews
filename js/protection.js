/**
 * Smart Anti-Crawler & Protection System (Daily Korean Shield)
 * Protects against automated scrapers while keeping normal user UX smooth.
 */

(function initProtection() {
  // 1. Invisible Honeypot Trap for Automated Scrapers/Crawlers
  document.addEventListener('DOMContentLoaded', () => {
    const honeypot = document.createElement('a');
    honeypot.href = '/trap-bot-do-not-follow.html';
    honeypot.className = 'bot-trap';
    honeypot.rel = 'nofollow';
    honeypot.setAttribute('aria-hidden', 'true');
    honeypot.textContent = 'Do not follow this link';
    document.body.appendChild(honeypot);
  });

  // 2. Silent Copyright Attribution on Copy Event (UX friendly)
  document.addEventListener('copy', (e) => {
    const selection = window.getSelection();
    if (!selection || selection.toString().length < 30) return;

    // Appends subtle source attribution without breaking copy functionality
    const copiedText = selection.toString() + "\n\n[출처: Daily Korean News (https://chaninjung.github.io/korean-dailynews/)]";
    if (e.clipboardData) {
      e.clipboardData.setData('text/plain', copiedText);
      e.preventDefault();
    }
  });
})();

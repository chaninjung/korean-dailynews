const translations = {
  kor: {
    brandName: "Daily Korean News",
    navTop: "Top",
    navCategory: "Category ▾",
    navMaterials: "Materials",
    heroTitle: "매일 업데이트되는 1:1 맞춤 한국어 데일리 레슨",
    catAll: "전체 (All)",
    catGlobal: "지구촌 & 사회",
    catTech: "테크 & 미래",
    catMind: "건강 & 심리",
    catCulture: "문화 & 예술",
    catTravel: "여행 & 라이프스타일",
    materialTitle: "LESSON MATERIALS",
    materialSubtitle: "난이도 레벨 또는 관심 분야별 교재 검색",
    searchPlaceholder: "예: 비즈니스, 회화, TOPIK...",
    levelBeginner: "Beginner (초급)",
    levelIntermediate: "Intermediate (중급)",
    levelAdvanced: "Advanced (고급)",
    levelProficient: "Proficient (최고급)",
    readLessonBtn: "교재 열람하기",
    closeBtn: "닫기",
    backBtn: "뒤로 가기",
    pastArticlesTitle: "Past Articles (지난 기사)",
    footerText: "© 2026 Daily Korean News. All rights reserved."
  },
  eng: {
    brandName: "Daily Korean News",
    navTop: "Top",
    navCategory: "Category ▾",
    navMaterials: "Materials",
    heroTitle: "Daily 1:1 Korean Lessons Updated Every Day",
    catAll: "All",
    catGlobal: "Global & Society",
    catTech: "Tech & Future",
    catMind: "Health & Mind",
    catCulture: "Culture & Arts",
    catTravel: "Travel & Lifestyle",
    materialTitle: "LESSON MATERIALS",
    materialSubtitle: "Search by level or interests.",
    searchPlaceholder: "e.g. Business, Conversation, TOPIK...",
    levelBeginner: "Beginner",
    levelIntermediate: "Intermediate",
    levelAdvanced: "Advanced",
    levelProficient: "Proficient",
    readLessonBtn: "Read Material",
    closeBtn: "Close",
    backBtn: "Back",
    pastArticlesTitle: "Past Articles",
    footerText: "© 2026 Daily Korean News. All rights reserved."
  },
  hu: {
    brandName: "Daily Korean News",
    navTop: "Top",
    navCategory: "Kategória ▾",
    navMaterials: "Tananyagok",
    heroTitle: "Naponta frissülő 1:1 koreai leckék és tananyagok",
    catAll: "Összes (All)",
    catGlobal: "Globális társadalom",
    catTech: "Technológia és Jövő",
    catMind: "Egészség és Elme",
    catCulture: "Kultúra és Művészet",
    catTravel: "Utazás és Életmód",
    materialTitle: "TANANYAGOK (LESSON MATERIALS)",
    materialSubtitle: "Keresés szint vagy érdeklődési kör alapján.",
    searchPlaceholder: "pl. Üzlet, Párbeszéd, TOPIK...",
    levelBeginner: "Kezdő (Beginner)",
    levelIntermediate: "Középhaladó (Intermediate)",
    levelAdvanced: "Haladó (Advanced)",
    levelProficient: "Mester (Proficient)",
    readLessonBtn: "Lecke megnyitása",
    closeBtn: "Bezárás",
    backBtn: "Vissza",
    pastArticlesTitle: "Korábbi cikkek (Past Articles)",
    footerText: "© 2026 Daily Korean News. Minden jog fenntartva."
  }
};

let currentLang = localStorage.getItem('daily_korean_lang') || 'kor';
window.currentLang = currentLang;

function setLanguage(lang) {
  if (!translations[lang]) return;
  currentLang = lang;
  window.currentLang = lang;
  localStorage.setItem('daily_korean_lang', lang);

  // Update active button state
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
  });

  // Apply translations to DOM elements with data-i18n attributes
  document.querySelectorAll('[data-i18n]').forEach(elem => {
    const key = elem.getAttribute('data-i18n');
    if (translations[lang][key]) {
      elem.textContent = translations[lang][key];
    }
  });

  // Apply placeholder translations
  document.querySelectorAll('[data-i18n-placeholder]').forEach(elem => {
    const key = elem.getAttribute('data-i18n-placeholder');
    if (translations[lang][key]) {
      elem.placeholder = translations[lang][key];
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  setLanguage(currentLang);
});


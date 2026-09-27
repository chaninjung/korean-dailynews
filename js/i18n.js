const translations = {
  kor: {
    brandName: "Daily Korean News",
    navTop: "Top",
    navCategory: "Category ▾",
    navMaterials: "Materials",
    heroTitle: "매일 업데이트되는 1:1 맞춤 한국어 데일리 레슨",
    catAll: "전체 (All)",
    catBusiness: "비즈니스 & 정치",
    catScience: "과학 & 기술",
    catHealth: "건강 & 라이프스타일",
    catCulture: "문화 & 사회",
    catTravel: "여행 & 문화 체험",
    materialTitle: "LESSON MATERIALS",
    materialSubtitle: "난이도 레벨 또는 관심 분야별 교재 검색",
    searchPlaceholder: "예: 비즈니스, 회화, TOPIK...",
    levelBeginner: "Beginner (초급)",
    levelIntermediate: "Intermediate (중급)",
    levelAdvanced: "Advanced (고급)",
    levelProficient: "Proficient (최고급)",
    readLessonBtn: "교재 열람하기",
    closeBtn: "닫기",
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
    catBusiness: "Business & Politics",
    catScience: "Science & Technology",
    catHealth: "Health & Lifestyle",
    catCulture: "Culture & Society",
    catTravel: "Travel & Experiences",
    materialTitle: "LESSON MATERIALS",
    materialSubtitle: "Search by level or interests.",
    searchPlaceholder: "e.g. Business, Conversation, TOPIK...",
    levelBeginner: "Beginner",
    levelIntermediate: "Intermediate",
    levelAdvanced: "Advanced",
    levelProficient: "Proficient",
    readLessonBtn: "Read Material",
    closeBtn: "Close",
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
    catBusiness: "Üzlet és Politika",
    catScience: "Tudomány és Technológia",
    catHealth: "Egészség és Életmód",
    catCulture: "Kultúra és Társadalom",
    catTravel: "Utazás és Élmények",
    materialTitle: "TANANYAGOK (LESSON MATERIALS)",
    materialSubtitle: "Keresés szint vagy érdeklődési kör alapján.",
    searchPlaceholder: "pl. Üzlet, Párbeszéd, TOPIK...",
    levelBeginner: "Kezdő (Beginner)",
    levelIntermediate: "Középhaladó (Intermediate)",
    levelAdvanced: "Haladó (Advanced)",
    levelProficient: "Mester (Proficient)",
    readLessonBtn: "Lecke megnyitása",
    closeBtn: "Bezárás",
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


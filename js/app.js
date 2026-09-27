let globalLessonsData = [];

document.addEventListener('DOMContentLoaded', async () => {
  const modal = document.getElementById('lessonModal');
  const modalClose = document.getElementById('modalClose');

  try {
    // Async Data Load via Security Layer
    globalLessonsData = await window.DailyKoreanShield.loadLessonData();
    renderLessonCards();
  } catch (err) {
    console.error("Data loading failed:", err);
  }

  // Modal close listeners
  if (modalClose) {
    modalClose.addEventListener('click', () => {
      modal.style.display = 'none';
    });
  }

  window.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.style.display = 'none';
    }
  });
});

function renderLessonCards() {
  const container = document.getElementById('lessons-container');
  if (!container || !globalLessonsData.length) return;

  const lang = window.currentLang || 'kor';
  container.innerHTML = '';

  globalLessonsData.forEach(lesson => {
    const card = document.createElement('div');
    card.className = 'lesson-card';

    const levelTagClass = `level-${lesson.level}`;
    const levelTextKey = `level${lesson.level.charAt(0).toUpperCase() + lesson.level.slice(1)}`;

    card.innerHTML = `
      <div>
        <span class="level-tag ${levelTagClass}" data-i18n="${levelTextKey}"></span>
        <h3>${lesson.title[lang] || lesson.title['eng']}</h3>
        <p>${lesson.desc[lang] || lesson.desc['eng']}</p>
      </div>
      <button class="btn-outline btn-read-lesson" onclick="openLessonModal('${lesson.id}')" data-i18n="readLessonBtn">교재 열람하기</button>
    `;

    container.appendChild(card);
  });

  // Re-apply current language labels
  if (typeof window.setLanguage === 'function') {
    window.setLanguage(lang);
  }
}

function openLessonModal(lessonId) {
  const lesson = globalLessonsData.find(l => l.id === lessonId);
  if (!lesson) return;

  const lang = window.currentLang || 'kor';
  const modal = document.getElementById('lessonModal');
  const modalTitle = document.getElementById('modal-lesson-title');
  const modalArticle = document.getElementById('modal-lesson-article');
  const modalVocabList = document.getElementById('modal-vocab-list');

  if (modalTitle) modalTitle.textContent = lesson.title[lang] || lesson.title['eng'];
  if (modalArticle) modalArticle.textContent = lesson.article[lang] || lesson.article['eng'];

  if (modalVocabList) {
    modalVocabList.innerHTML = '';
    lesson.vocab.forEach(v => {
      const li = document.createElement('li');
      li.textContent = v;
      modalVocabList.appendChild(li);
    });
  }

  modal.style.display = 'flex';
}

// Override setLanguage to re-render cards dynamically
const originalSetLanguage = window.setLanguage;
window.setLanguage = function (lang) {
  if (typeof originalSetLanguage === 'function') {
    originalSetLanguage(lang);
  }
  if (globalLessonsData && globalLessonsData.length) {
    // Refresh card content text
    renderLessonCards();
  }
};

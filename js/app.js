let globalLessonsData = [];

document.addEventListener('DOMContentLoaded', async () => {
  const modal = document.getElementById('lessonModal');
  const modalClose = document.getElementById('modalClose');

  try {
    // Async Data Load via Security Layer
    globalLessonsData = await window.DailyKoreanShield.loadLessonData();
    renderFeaturedGrid(globalLessonsData);
    renderCategorySections(globalLessonsData);
  } catch (err) {
    console.error("Data loading failed:", err);
  }

  // Event Listeners for Nav Menu links
  initNavigation();

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

function initNavigation() {
  const navTop = document.getElementById('nav-top');
  const navCategoryToggle = document.getElementById('nav-category-toggle');
  const categoryDropdown = document.getElementById('category-dropdown');
  const navMaterials = document.getElementById('nav-materials');

  const mainNewsView = document.getElementById('view-daily-news');
  const materialsView = document.getElementById('view-materials');

  // Top Click -> Show Daily News View
  if (navTop) {
    navTop.addEventListener('click', (e) => {
      e.preventDefault();
      mainNewsView.classList.remove('hidden');
      materialsView.classList.add('hidden');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // Category Dropdown Toggle
  if (navCategoryToggle && categoryDropdown) {
    navCategoryToggle.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      categoryDropdown.classList.toggle('show');
    });

    document.addEventListener('click', () => {
      categoryDropdown.classList.remove('show');
    });
  }

  // Materials Click -> Show Materials View (Photo 3)
  if (navMaterials) {
    navMaterials.addEventListener('click', (e) => {
      e.preventDefault();
      mainNewsView.classList.add('hidden');
      materialsView.classList.remove('hidden');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }
}

function renderFeaturedGrid(newsList) {
  const leftCardContainer = document.getElementById('featured-left-card-container');
  const rightGridContainer = document.getElementById('featured-right-grid-container');

  if (!newsList || !newsList.length) return;
  const lang = window.currentLang || 'kor';

  // 1st Item (Large Left)
  const mainItem = newsList[0];
  if (leftCardContainer) {
    leftCardContainer.innerHTML = `
      <div class="featured-left-card" onclick="openLessonModal('${mainItem.id}')">
        <img class="card-bg-img" src="${mainItem.image}" alt="${mainItem.title[lang]}">
        <div class="card-overlay">
          ${mainItem.isNew ? '<span class="badge-new">NEW</span>' : ''}
          <div class="card-bottom-info">
            <h2 class="card-title">${mainItem.title[lang] || mainItem.title['eng']}</h2>
            <div class="card-meta-bar">
              <span class="level-badge"><span class="level-badge-num">${mainItem.levelNum}</span> ${mainItem.level}</span>
              <span class="category-tag">${mainItem.category}</span>
              ${mainItem.date ? `<span class="date-tag">📅 ${mainItem.date}</span>` : ''}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // Items 2~5 (Right 2x2 Grid)
  if (rightGridContainer) {
    rightGridContainer.innerHTML = '';
    const rightItems = newsList.slice(1, 5);

    rightItems.forEach(item => {
      const card = document.createElement('div');
      card.className = 'featured-card-small';
      card.onclick = () => openLessonModal(item.id);

      card.innerHTML = `
        <img class="card-bg-img" src="${item.image}" alt="${item.title[lang]}">
        <div class="card-overlay">
          ${item.isNew ? '<span class="badge-new">NEW</span>' : ''}
          <div class="card-bottom-info">
            <h3 class="card-title">${item.title[lang] || item.title['eng']}</h3>
            <div class="card-meta-bar">
              <span class="level-badge"><span class="level-badge-num">${item.levelNum}</span> ${item.level}</span>
              <span class="category-tag">${item.category}</span>
              ${item.date ? `<span class="date-tag">📅 ${item.date}</span>` : ''}
            </div>
          </div>
        </div>
      `;

      rightGridContainer.appendChild(card);
    });
  }
}

function renderCategorySections(newsList) {
  const container = document.getElementById('category-sections-container');
  if (!container || !newsList.length) return;

  const lang = window.currentLang || 'kor';
  container.innerHTML = '';

  // Group by category
  const categories = ["Business & Politics", "Science & Technology", "Culture & Society", "Travel & Experiences"];

  categories.forEach(cat => {
    const catItems = newsList.filter(item => item.category === cat);
    if (!catItems.length) return;

    const sec = document.createElement('div');
    sec.className = 'category-section';

    sec.innerHTML = `
      <div class="section-title-bar">
        <span>🏷️</span>
        <span>${cat}</span>
      </div>
      <div class="articles-row">
        ${catItems.map(item => `
          <div class="article-card-standard" onclick="openLessonModal('${item.id}')">
            <img class="article-card-thumb" src="${item.image}" alt="${item.title[lang]}">
            <div class="article-card-body">
              <div class="article-card-title">${item.title[lang] || item.title['eng']}</div>
              <div class="card-meta-bar" style="margin-top: 8px;">
                <span class="level-badge"><span class="level-badge-num">${item.levelNum}</span> ${item.level}</span>
                ${item.date ? `<span class="date-tag">📅 ${item.date}</span>` : ''}
                ${item.isNew ? '<span class="badge-new">NEW</span>' : ''}
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    `;

    container.appendChild(sec);
  });
}

function filterCategory(categoryName) {
  const mainNewsView = document.getElementById('view-daily-news');
  const materialsView = document.getElementById('view-materials');
  
  mainNewsView.classList.remove('hidden');
  materialsView.classList.add('hidden');

  if (categoryName === 'All') {
    renderFeaturedGrid(globalLessonsData);
    renderCategorySections(globalLessonsData);
  } else {
    const filtered = globalLessonsData.filter(item => item.category === categoryName);
    renderFeaturedGrid(filtered.length ? filtered : globalLessonsData);
    renderCategorySections(filtered);
  }

  const categoryDropdown = document.getElementById('category-dropdown');
  if (categoryDropdown) categoryDropdown.classList.remove('show');
}

function openLessonModal(lessonId) {
  // Navigate to dedicated article page with unique URL
  window.location.href = `article.html?id=${lessonId}`;
}

// Override setLanguage to re-render texts dynamically
const originalSetLanguage = window.setLanguage;
window.setLanguage = function (lang) {
  if (typeof originalSetLanguage === 'function') {
    originalSetLanguage(lang);
  }
  if (globalLessonsData && globalLessonsData.length) {
    renderFeaturedGrid(globalLessonsData);
    renderCategorySections(globalLessonsData);
  }
};

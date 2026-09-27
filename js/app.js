document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('lessonModal');
  const modalClose = document.getElementById('modalClose');

  document.querySelectorAll('.btn-read-lesson').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      modal.style.display = 'flex';
    });
  });

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

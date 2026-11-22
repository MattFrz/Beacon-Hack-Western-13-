const gallery = document.querySelector('.gallery');
const slidePickers = [...gallery.querySelectorAll('[aria-controls]')];
const slides = slidePickers.map((button) => document.getElementById(button.getAttribute('aria-controls')));
const video = gallery.querySelector('video');
const announcement = gallery.querySelector('#gallery-status');
let current = 0;

function showSlide(index) {
  if (index === current) return;
  if (slides[current].contains(video)) video.pause();
  slides[current].hidden = true;
  slidePickers[current].setAttribute('aria-pressed', 'false');
  current = index;
  slides[current].hidden = false;
  slidePickers[current].setAttribute('aria-pressed', 'true');
  announcement.textContent = slides[current].getAttribute('aria-label') + ', ' +
    (current + 1) + ' of ' + slides.length;
}

function stepSlide(step) {
  showSlide((current + step + slides.length) % slides.length);
}

slidePickers.forEach((button, index) => {
  button.addEventListener('click', () => showSlide(index));
});

gallery.querySelectorAll('[data-step]').forEach((button) => {
  button.addEventListener('click', () => stepSlide(Number(button.dataset.step)));
});

gallery.addEventListener('keydown', (event) => {
  if (!event.target.closest('button')) return;
  if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
    event.preventDefault();
    stepSlide(event.key === 'ArrowLeft' ? -1 : 1);
  }
});

gallery.querySelector('.gallery-arrows').hidden = false;
gallery.querySelector('.gallery-pickers').hidden = false;

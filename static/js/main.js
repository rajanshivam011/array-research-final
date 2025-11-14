// Wait until DOM fully loads
document.addEventListener("DOMContentLoaded", function() {

  /* --- PARTICLES BACKGROUND --- */
  if (document.getElementById("particles-js")) {
    particlesJS.load('particles-js', '/static/js/particles.json', () => {
      console.log("✅ Particles Loaded");
    });
  }

  /* --- COUNTER ANIMATION --- */
  const counters = document.querySelectorAll(".stat-number");

  counters.forEach(counter => {
    let target = +counter.getAttribute("data-count");
    let count = 0;
    let step = target / 80;

    let interval = setInterval(() => {
      count += step;
      counter.innerText = Math.floor(count);
      if (count >= target) clearInterval(interval);
    }, 20);
  });

  /* --- SWIPER TESTIMONIALS --- */
  if (document.querySelector(".swiper")) {
    new Swiper(".swiper", {
      loop: true,
      autoplay: { delay: 2800 },
      pagination: { el: ".swiper-pagination", clickable: true },
      speed: 600
    });
  }

});
// ----- ABOUT counters (animate when visible) -----
(function () {
  const counters = document.querySelectorAll(".count[data-target]");
  if (!counters.length) return;

  const animate = (el) => {
    const target = +el.getAttribute("data-target");
    const duration = 1200; // ms
    const start = performance.now();

    const step = (t) => {
      const p = Math.min((t - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3); // easeOutCubic
      el.textContent = Math.floor(eased * target).toLocaleString();
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          animate(e.target);
          io.unobserve(e.target);
        }
      });
    },
    { threshold: 0.3 }
  );

  counters.forEach((c) => io.observe(c));
})();

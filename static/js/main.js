// main.js — global UI behaviors shared across every page.
(function () {
  "use strict";

  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Theme toggle (persists via localStorage) ---------- */
  const root = document.documentElement;
  const themeToggle = document.getElementById("themeToggle");
  const savedTheme = localStorage.getItem("veritas-theme");
  if (savedTheme) root.setAttribute("data-theme", savedTheme);

  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      const next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
      root.setAttribute("data-theme", next);
      localStorage.setItem("veritas-theme", next);
    });
  }

  /* ---------- Mobile nav toggle ---------- */
  const navToggle = document.getElementById("navToggle");
  const navLinks = document.getElementById("navLinks");
  if (navToggle && navLinks) {
    navToggle.addEventListener("click", function () {
      const isOpen = navLinks.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", String(isOpen));
    });
    navLinks.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => navLinks.classList.remove("is-open"));
    });
  }

  /* ---------- Flash message dismiss ---------- */
  document.querySelectorAll(".flash-close").forEach((btn) => {
    btn.addEventListener("click", function () {
      const flash = btn.closest(".flash");
      if (flash) {
        flash.style.transition = "opacity 0.3s ease, transform 0.3s ease";
        flash.style.opacity = "0";
        flash.style.transform = "translateY(-6px)";
        setTimeout(() => flash.remove(), 300);
      }
    });
  });
  // Auto-dismiss flashes after 6s
  setTimeout(() => {
    document.querySelectorAll(".flash-close").forEach((btn) => btn.click());
  }, 6000);

  /* ---------- Scroll reveal ---------- */
  const revealEls = document.querySelectorAll(".reveal");
  if (revealEls.length) {
    if (prefersReducedMotion || !("IntersectionObserver" in window)) {
      revealEls.forEach((el) => el.classList.add("is-visible"));
    } else {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry, i) => {
            if (entry.isIntersecting) {
              setTimeout(() => entry.target.classList.add("is-visible"), i * 40);
              observer.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
      );
      revealEls.forEach((el) => observer.observe(el));
    }
  }

  /* ---------- Animated stat counters ---------- */
  const statNumbers = document.querySelectorAll(".stat-number[data-count]");
  if (statNumbers.length && !prefersReducedMotion) {
    const animateCount = (el) => {
      const target = parseInt(el.getAttribute("data-count"), 10) || 0;
      const suffix = el.querySelector(".stat-suffix");
      const duration = 900;
      const start = performance.now();
      function tick(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = Math.floor(eased * target);
        el.childNodes[0].nodeValue = value.toLocaleString();
        if (progress < 1) requestAnimationFrame(tick);
        else el.childNodes[0].nodeValue = target.toLocaleString();
      }
      requestAnimationFrame(tick);
    };
    const counterObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          animateCount(entry.target);
          counterObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.4 });
    statNumbers.forEach((el) => counterObserver.observe(el));
  } else {
    statNumbers.forEach((el) => {
      const target = parseInt(el.getAttribute("data-count"), 10) || 0;
      el.childNodes[0].nodeValue = target.toLocaleString();
    });
  }

  /* ---------- Typing effect (home hero) ---------- */
  const typingEl = document.getElementById("typingText");
  if (typingEl && !prefersReducedMotion) {
    const samples = [
      '"Scientists confirm new discovery after peer review."',
      '"You won\'t believe this secret they don\'t want you to know!!!"',
      '"Central bank announces quarterly interest rate decision."',
    ];
    let sampleIndex = 0, charIndex = 0, deleting = false;

    function loopType() {
      const current = samples[sampleIndex];
      if (!deleting) {
        charIndex++;
        typingEl.textContent = current.slice(0, charIndex);
        if (charIndex === current.length) {
          deleting = true;
          setTimeout(loopType, 1600);
          return;
        }
      } else {
        charIndex--;
        typingEl.textContent = current.slice(0, charIndex);
        if (charIndex === 0) {
          deleting = false;
          sampleIndex = (sampleIndex + 1) % samples.length;
        }
      }
      setTimeout(loopType, deleting ? 22 : 42);
    }
    loopType();
  }
})();

(function () {
  "use strict";

  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const header = document.querySelector("[data-header]");
  const toggle = document.querySelector(".nav-toggle");
  const loader = document.getElementById("loader");
  const THEME_KEY = "kp-theme";

  const getTheme = () =>
    document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";

  const updateThemeUI = (theme) => {
    document.querySelectorAll("[data-theme-label]").forEach((el) => {
      el.textContent = theme === "dark" ? "Dark" : "Light";
    });
    document.querySelectorAll("[data-theme-set]").forEach((btn) => {
      const active = btn.getAttribute("data-theme-set") === theme;
      btn.setAttribute("aria-selected", active ? "true" : "false");
    });
  };

  const setTheme = (theme) => {
    const next = theme === "dark" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch (e) {}
    updateThemeUI(next);
  };

  updateThemeUI(getTheme());

  document.querySelectorAll("[data-theme-dropdown]").forEach((dropdown) => {
    const trigger = dropdown.querySelector(".theme-trigger");
    const menu = dropdown.querySelector(".theme-menu");
    if (!trigger || !menu) return;

    trigger.addEventListener("click", (e) => {
      e.stopPropagation();
      const open = dropdown.classList.toggle("is-open");
      trigger.setAttribute("aria-expanded", open ? "true" : "false");
      if (open) menu.removeAttribute("hidden");
      else menu.setAttribute("hidden", "");
    });

    menu.querySelectorAll("[data-theme-set]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        setTheme(btn.getAttribute("data-theme-set"));
        dropdown.classList.remove("is-open");
        trigger.setAttribute("aria-expanded", "false");
        menu.setAttribute("hidden", "");
      });
    });
  });

  document.addEventListener("click", () => {
    document.querySelectorAll("[data-theme-dropdown]").forEach((dropdown) => {
      dropdown.classList.remove("is-open");
      const trigger = dropdown.querySelector(".theme-trigger");
      const menu = dropdown.querySelector(".theme-menu");
      if (trigger) trigger.setAttribute("aria-expanded", "false");
      if (menu) menu.setAttribute("hidden", "");
    });
  });

  // Crest loader
  const finishLoader = () => {
    if (!loader) return;
    loader.classList.add("is-done");
    loader.setAttribute("aria-hidden", "true");
  };
  if (reduce) {
    finishLoader();
  } else {
    window.addEventListener("load", () => setTimeout(finishLoader, 700));
    setTimeout(finishLoader, 2200);
  }

  // Sticky header
  const onScroll = () => {
    if (!header) return;
    header.classList.toggle("scrolled", window.scrollY > 20);
  };
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  // Mobile nav
  if (toggle && header) {
    toggle.addEventListener("click", () => {
      const open = header.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      document.body.style.overflow = open ? "hidden" : "";
    });
    header.querySelectorAll(".nav-drawer a").forEach((a) => {
      a.addEventListener("click", () => {
        header.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
        document.body.style.overflow = "";
      });
    });
  }

  // Reveal
  if (!reduce && "IntersectionObserver" in window) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -6% 0px" }
    );
    document.querySelectorAll(".reveal").forEach((el) => io.observe(el));
  } else {
    document.querySelectorAll(".reveal").forEach((el) => el.classList.add("in"));
  }

  // Count-up
  if (!reduce) {
    const animate = (el) => {
      const target = Number(el.getAttribute("data-count"));
      const suffix = el.getAttribute("data-suffix") || "";
      const prefix = el.getAttribute("data-prefix") || "";
      const start = performance.now();
      const dur = 1400;
      const tick = (now) => {
        const t = Math.min(1, (now - start) / dur);
        const eased = 1 - Math.pow(1 - t, 3);
        el.textContent = prefix + Math.round(target * eased) + suffix;
        if (t < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    };
    if ("IntersectionObserver" in window) {
      const cio = new IntersectionObserver(
        (entries) => {
          entries.forEach((e) => {
            if (e.isIntersecting) {
              animate(e.target);
              cio.unobserve(e.target);
            }
          });
        },
        { threshold: 0.45 }
      );
      document.querySelectorAll("[data-count]").forEach((el) => cio.observe(el));
    }
  }

  // Soft parallax on vision background
  const visionBg = document.querySelector(".vision-bg");
  if (visionBg && !reduce) {
    window.addEventListener(
      "scroll",
      () => {
        const rect = visionBg.parentElement.getBoundingClientRect();
        if (rect.bottom < 0 || rect.top > window.innerHeight) return;
        const p = (window.innerHeight - rect.top) / (window.innerHeight + rect.height);
        visionBg.style.transform = "scale(1.08) translateY(" + (p - 0.5) * 36 + "px)";
      },
      { passive: true }
    );
  }

  // Home bio Read More / Read Less (matches live site pattern)
  const bioToggle = document.getElementById("bio-toggle");
  const bioMore = document.getElementById("bio-more");
  if (bioToggle && bioMore) {
    bioToggle.addEventListener("click", () => {
      const open = bioToggle.getAttribute("aria-expanded") === "true";
      const next = !open;
      bioToggle.setAttribute("aria-expanded", next ? "true" : "false");
      if (next) bioMore.removeAttribute("hidden");
      else bioMore.setAttribute("hidden", "");
      bioToggle.innerHTML = next
        ? 'Read Less <span aria-hidden="true">▲</span>'
        : 'Read More <span aria-hidden="true">▼</span>';
    });
  }

  // Active section
  const sections = document.querySelectorAll("main section[id]");
  const links = document.querySelectorAll('.nav-links a[href^="#"]');
  if (sections.length && links.length && "IntersectionObserver" in window) {
    const sio = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (!e.isIntersecting) return;
          const id = e.target.id;
          links.forEach((a) => {
            if (a.getAttribute("href") === "#" + id) a.setAttribute("aria-current", "page");
            else a.removeAttribute("aria-current");
          });
        });
      },
      { rootMargin: "-40% 0px -50% 0px", threshold: 0 }
    );
    sections.forEach((s) => sio.observe(s));
  }
})();

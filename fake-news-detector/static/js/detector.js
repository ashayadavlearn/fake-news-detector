// detector.js — powers the Detect / Clear / Sample news buttons on /detector
(function () {
  "use strict";

  const textarea = document.getElementById("newsText");
  const charCount = document.getElementById("charCount");
  const form = document.getElementById("detectorForm");
  const detectBtn = document.getElementById("detectBtn");
  const clearBtn = document.getElementById("clearBtn");
  const sampleBtn = document.getElementById("sampleBtn");
  const resultCard = document.getElementById("resultCard");

  if (!textarea || !form) return;

  function updateCharCount() {
    if (charCount) charCount.textContent = textarea.value.length.toLocaleString();
  }
  textarea.addEventListener("input", updateCharCount);
  updateCharCount();

  clearBtn.addEventListener("click", function () {
    textarea.value = "";
    updateCharCount();
    textarea.focus();
  });

  sampleBtn.addEventListener("click", function () {
    const samples = window.SAMPLE_NEWS || {};
    const pool = [samples.real, samples.fake].filter(Boolean);
    if (!pool.length) return;
    textarea.value = pool[Math.floor(Math.random() * pool.length)];
    updateCharCount();
    textarea.focus();
  });

  function setLoading(isLoading) {
    if (isLoading) {
      detectBtn.classList.add("is-loading");
      detectBtn.disabled = true;
    } else {
      detectBtn.classList.remove("is-loading");
      detectBtn.disabled = false;
    }
  }

  function renderResult(data) {
    const verdictEl = document.getElementById("verdictLabel");
    const confidenceValue = document.getElementById("confidenceValue");
    const confidenceFill = document.getElementById("confidenceFill");
    const modelUsed = document.getElementById("modelUsed");
    const entryId = document.getElementById("entryId");

    const isReal = data.label === "REAL";
    verdictEl.textContent = isReal ? "Real News ✅" : "Fake News ❌";
    verdictEl.classList.toggle("is-real", isReal);
    verdictEl.classList.toggle("is-fake", !isReal);

    confidenceValue.textContent = data.confidence + "%";
    confidenceFill.style.width = "0%";
    confidenceFill.classList.toggle("is-real", isReal);
    confidenceFill.classList.toggle("is-fake", !isReal);
    // Force reflow so the width transition replays every time
    void confidenceFill.offsetWidth;
    requestAnimationFrame(() => { confidenceFill.style.width = data.confidence + "%"; });

    modelUsed.textContent = data.model_used;
    entryId.textContent = data.id;

    resultCard.classList.add("has-result");
    const content = document.getElementById("resultContent");
    content.setAttribute("data-visible", "true");
  }

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    if (!textarea.value.trim()) {
      textarea.focus();
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData(form);
      const response = await fetch("/api/detect", {
        method: "POST",
        body: formData,
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      const data = await response.json();

      if (!response.ok || !data.ok) {
        alert((data.errors && data.errors[0]) || "Something went wrong. Please try again.");
        return;
      }
      renderResult(data);
    } catch (err) {
      alert("Network error — please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  });
})();

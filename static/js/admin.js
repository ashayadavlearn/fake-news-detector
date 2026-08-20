// admin.js — renders the distribution doughnut chart on the admin dashboard.
(function () {
  "use strict";

  const canvas = document.getElementById("distributionChart");
  if (!canvas || typeof Chart === "undefined" || !window.CHART_DATA) return;

  const data = window.CHART_DATA;
  const styles = getComputedStyle(document.documentElement);

  new Chart(canvas.getContext("2d"), {
    type: "doughnut",
    data: {
      labels: ["Real news", "Fake news"],
      datasets: [{
        data: [data.real, data.fake],
        backgroundColor: [
          styles.getPropertyValue("--real-500").trim() || "#35d68f",
          styles.getPropertyValue("--fake-500").trim() || "#ff5d7a",
        ],
        borderWidth: 0,
        hoverOffset: 6,
      }],
    },
    options: {
      responsive: true,
      cutout: "68%",
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: styles.getPropertyValue("--text-mid").trim() || "#ccc",
            padding: 16,
            font: { family: "Inter", size: 12 },
          },
        },
      },
    },
  });
})();

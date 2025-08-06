  document.addEventListener("DOMContentLoaded", function() {
    const rows = document.querySelectorAll(".clickable-row");
    rows.forEach(row => {
      row.addEventListener("click", () => {
        window.location.href = row.dataset.href;
      });
      row.style.cursor = "pointer";
    });
  });
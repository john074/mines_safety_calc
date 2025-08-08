  document.addEventListener("DOMContentLoaded", function() {
    const rows = document.querySelectorAll(".clickable-row");
    rows.forEach(row => {
      row.addEventListener("click", () => {
        window.location.href = row.dataset.href;
      });
      row.style.cursor = "pointer";
    });
  });


document.addEventListener('DOMContentLoaded', function () {
    const pageData = document.getElementById('page-data');
    const saveUrl = pageData.dataset.saveUrl;
    const calcId = pageData.dataset.calcId;
    const csrfToken = pageData.dataset.csrfToken;

    function saveField(paramId, fieldType, value) {
        fetch(saveUrl, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                calc_id: calcId,
                param_id: paramId,
                field_type: fieldType,
                value: value
            })
        })
        .then(r => r.json())
        .then(data => {
            if (!data.success) {
                console.error("Save err:", data.error);
            }
        })
        .catch(err => console.error("Network err:", err));
    }

    document.querySelectorAll('select[data-param-id]').forEach(function(select) {
        select.addEventListener('change', function () {
            saveField(this.dataset.paramId, this.dataset.fieldType, this.value);
        });
    });

    document.querySelectorAll('textarea[data-param-id]').forEach(function(textarea) {
        textarea.addEventListener('input', function () {
            saveField(this.dataset.paramId, this.dataset.fieldType, this.value);
        });
    });
});

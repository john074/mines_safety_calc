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

document.addEventListener("DOMContentLoaded", function() {
    const finishBtn = document.getElementById("finish-btn");
    const modal = document.getElementById("finish-modal");
    const cancelBtn = document.getElementById("cancel-btn");
    const confirmBtn = document.getElementById("confirm-btn");
    const form = document.getElementById("rx-form");

    if (finishBtn) {
        finishBtn.addEventListener("click", function() {
            modal.style.display = "flex";
        });
    }

    cancelBtn.addEventListener("click", function() {
        modal.style.display = "none";
    });

    confirmBtn.addEventListener("click", function() {
        const hiddenInput = document.createElement("input");
        hiddenInput.type = "hidden";
        hiddenInput.name = "confirm_finish";
        hiddenInput.value = "1";
        form.appendChild(hiddenInput);
        form.submit();
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const innInput = document.getElementById("inn");

    innInput.addEventListener("input", function () {
        const inn = innInput.value.trim();

        if (/^\d{10}$|^\d{12}$/.test(inn)) {
            fetch(`/calculations/fill_by_inn/${inn}/`, {
                headers: { "X-Requested-With": "XMLHttpRequest" }
            })
            .then(resp => resp.json())
            .then(data => {
                if (data.found) {
                    document.getElementById("name").value = data.name || "";
                    document.getElementById("kpp").value = data.kpp || "";
                    document.getElementById("ogrn").value = data.ogrn || "";
                    document.getElementById("address").value = data.address || "";
                }
            })
            .catch(err => console.error("Ошибка загрузки данных:", err));
        }
    });
});

function toggleClass(target_id, self_id) {
    const element = document.getElementById(target_id);
    const checkbox = document.getElementById(self_id);
    
    if (checkbox.checked) {
        element.classList.remove("print-button");
    } else {
        element.classList.add("print-button");
    }
}

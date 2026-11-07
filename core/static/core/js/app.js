/* Демонстрации для ДЗ2: данные не сохраняются. */
"use strict";

// Повторный клик отменяет голос, переголосование учитывает прошлый выбор.
document.querySelectorAll(".vote-widget").forEach((widget) => {
    const buttons = widget.querySelectorAll("[data-vote]");
    const counter = widget.querySelector(".vote-count");
    let currentVote = Number(widget.dataset.currentVote || 0);
    let score = Number(counter.textContent);
    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            const clickedVote = Number(button.dataset.vote);
            const nextVote = currentVote === clickedVote ? 0 : clickedVote;
            score += nextVote - currentVote;
            currentVote = nextVote;
            widget.dataset.currentVote = String(currentVote);
            counter.textContent = String(score);
            buttons.forEach((item) => {
                item.setAttribute("aria-pressed", String(Number(item.dataset.vote) === currentVote));
            });
        });
    });
});

// Стандартные checkbox: выбрать можно только один правильный ответ.
document.querySelectorAll(".accept-input").forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
        const selected = checkbox.checked;
        document.querySelectorAll(".accept-input").forEach((item) => {
            item.checked = item === checkbox && selected;
            item.closest(".answer-card").dataset.accepted = String(item.checked);
        });
    });
});

// Валидация полей и общий результат. Корректные данные НЕ сохраняются.
document.querySelectorAll("[data-demo-form]").forEach((form) => {
    const controls = [...form.querySelectorAll('input:not([type="hidden"]):not([readonly]), textarea')];
    const summary = form.querySelector("[data-form-error]");
    const success = form.querySelector("[data-form-success]");
    function extraError(control) {
        if (control.name === "tags") {
            const tags = control.value.split(",").map((tag) => tag.trim()).filter(Boolean);
            if (!tags.length) return "Укажи хотя бы один тег.";
            if (tags.length > 3) return "Можно указать не более трёх тегов.";
        }
        if (control.name === "password_confirm") {
            if (control.value !== form.querySelector('[name="password"]').value) return "Пароли не совпадают.";
        }
        if (control.type === "file" && control.files.length) {
            const file = control.files[0];
            if (!["image/png", "image/jpeg", "image/webp"].includes(file.type)) return "Выберите PNG, JPEG или WebP.";
            if (file.size > 2 * 1024 * 1024) return "Размер файла должен быть не больше 2 МБ.";
        }
        if (control.required && !control.value.trim()) return "Заполните это поле.";
        if (control.minLength > 0 && control.value.trim().length < control.minLength) return `Введите не менее ${control.minLength} символов.`;
        return "";
    }
    controls.forEach((control) => {
        control.addEventListener("input", () => {
            control.setCustomValidity("");
            control.classList.remove("is-invalid");
            control.removeAttribute("aria-invalid");
            success.hidden = true;
        });
    });
    form.addEventListener("submit", (event) => {
        event.preventDefault();
        let firstInvalid = null;
        controls.forEach((control) => {
            control.setCustomValidity(extraError(control));
            const invalid = !control.checkValidity();
            control.classList.toggle("is-invalid", invalid);
            control.setAttribute("aria-invalid", String(invalid));
            if (invalid) {
                firstInvalid ||= control;
                const feedback = document.getElementById(control.dataset.feedback);
                if (feedback) feedback.textContent = control.validationMessage;
            }
        });
        summary.hidden = !firstInvalid;
        success.hidden = Boolean(firstInvalid);
        if (firstInvalid) {
            firstInvalid.focus();
        } else {
            // Результат виден и тем, кто заполняет длинную форму на телефоне.
            success.scrollIntoView({ block: "nearest" });
        }
    });
});

// Локальный предпросмотр аватара.
document.querySelectorAll("[data-avatar-input]").forEach((input) => {
    const preview = document.getElementById(input.dataset.avatarInput);
    const originalSrc = preview.src;
    let objectUrl;
    input.addEventListener("change", () => {
        const file = input.files[0];
        if (!file || !["image/png", "image/jpeg", "image/webp"].includes(file.type) || file.size > 2 * 1024 * 1024) {
            if (objectUrl) {
                URL.revokeObjectURL(objectUrl);
                objectUrl = undefined;
                preview.src = originalSrc;
            }
            return;
        }
        if (objectUrl) URL.revokeObjectURL(objectUrl);
        objectUrl = URL.createObjectURL(file);
        preview.src = objectUrl;
    });
});

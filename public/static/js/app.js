/* Демонстрации статической вёрстки ДЗ1: данные не сохраняются. */
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

// Пагинация переключает заранее свёрстанные примеры.
document.querySelectorAll("[data-pagination]").forEach((navigation) => {
    const group = navigation.dataset.pagination;
    const panels = document.querySelectorAll(`[data-page-group="${group}"]`);
    const links = navigation.querySelectorAll("[data-page]");
    links.forEach((link) => {
        link.addEventListener("click", (event) => {
            event.preventDefault();
            const page = link.dataset.page;
            panels.forEach((panel) => { panel.hidden = panel.dataset.page !== page; });
            links.forEach((item) => {
                const active = item === link;
                item.parentElement.classList.toggle("active", active);
                if (active) item.setAttribute("aria-current", "page");
                else item.removeAttribute("aria-current");
            });
        });
    });
});

// Локальные фильтры не обращаются к серверу.
const params = new URLSearchParams(window.location.search);
const selectedTag = params.get("tag") || "bootstrap";
const query = params.get("q");
if (document.body.dataset.page === "tag" && selectedTag) {
    document.querySelector("#selected-tag").textContent = selectedTag;
    document.title = `Тег ${selectedTag} — Ответы`;
    document.querySelectorAll("[data-tags]").forEach((card) => {
        card.hidden = !card.dataset.tags.split(",").includes(selectedTag.toLowerCase());
    });
}
if (document.body.dataset.page === "index" && query && query.trim()) {
    document.querySelector("#listing-title").textContent = `Поиск: ${query}`;
    document.querySelector(".header-search input").value = query;
    document.querySelectorAll('[data-page-group="questions"]').forEach((panel) => { panel.hidden = false; });
    document.querySelector('[data-pagination="questions"]').hidden = true;
    document.querySelectorAll("[data-tags]").forEach((card) => {
        card.hidden = !card.textContent.toLowerCase().includes(query.trim().toLowerCase());
    });
}
const cards = [...document.querySelectorAll("[data-tags]")];
if (cards.length && cards.every((card) => card.hidden)) {
    document.querySelector("#empty-list").hidden = false;
}

// Валидация полей и общий результат. Корректные данные НЕ сохраняются.
document.querySelectorAll("[data-demo-form]").forEach((form) => {
    const controls = [...form.querySelectorAll("input, textarea")];
    const summary = form.querySelector("[data-form-error]");
    const success = form.querySelector("[data-form-success]");
    function extraError(control) {
        if (control.name === "tags") {
            const tags = control.value.split(",").map((tag) => tag.trim()).filter(Boolean);
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
    let objectUrl;
    input.addEventListener("change", () => {
        const file = input.files[0];
        if (!file || !["image/png", "image/jpeg", "image/webp"].includes(file.type) || file.size > 2 * 1024 * 1024) return;
        if (objectUrl) URL.revokeObjectURL(objectUrl);
        objectUrl = URL.createObjectURL(file);
        document.getElementById(input.dataset.avatarInput).src = objectUrl;
    });
});

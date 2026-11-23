"use strict";

async function postAction(url, fields) {
    const csrf = document.querySelector('input[name="csrfmiddlewaretoken"]');
    const response = await fetch(url, {
        method: "POST",
        headers: { "X-CSRFToken": csrf.value, "Accept": "application/json" },
        body: new URLSearchParams(fields),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Не удалось сохранить изменения.");
    return result;
}

document.querySelectorAll(".vote-widget").forEach((widget) => {
    const buttons = [...widget.querySelectorAll("[data-vote]")];
    widget.addEventListener("click", async (event) => {
        const selected = event.target.closest("[data-vote]");
        if (!selected || selected.disabled) return;
        buttons.forEach(button => { button.disabled = true; });
        try {
            const data = await postAction(widget.dataset.url, { value: selected.dataset.vote });
            widget.querySelector(".vote-count").textContent = data.score;
            buttons.forEach(button => {
                const active = Number(button.dataset.vote) === data.vote;
                button.setAttribute("aria-pressed", String(active));
                button.title = active ? "Эта оценка уже поставлена" : "";
            });
        } catch (error) {
            window.alert(error.message);
        } finally {
            buttons.forEach(button => { button.disabled = button.getAttribute("aria-pressed") === "true"; });
        }
    });
});

const choices = [...document.querySelectorAll(".accept-input")];
choices.forEach((choice) => {
    choice.addEventListener("change", async () => {
        const desired = choice.checked;
        choices.forEach(input => { input.disabled = true; });
        try {
            const data = await postAction(choice.dataset.url, {
                answer: choice.dataset.answer, accepted: desired ? "1" : "0",
            });
            choices.forEach(input => {
                if (data.accepted || Number(input.dataset.answer) === data.answer) {
                    input.checked = data.accepted && Number(input.dataset.answer) === data.answer;
                    input.closest(".answer-card").dataset.accepted = String(input.checked);
                }
            });
        } catch (error) {
            choice.checked = !desired;
            window.alert(error.message);
        } finally {
            choices.forEach(input => { input.disabled = false; });
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

const chatArea = document.getElementById("chatArea");
const msgInput = document.getElementById("msgInput");
const sendBtn = document.getElementById("sendBtn");
const settingsBtn = document.getElementById("settingsBtn");
const settingsModal = document.getElementById("settingsModal");
const closeSettings = document.getElementById("closeSettings");
const saveSettings = document.getElementById("saveSettings");
const resetDefaults = document.getElementById("resetDefaults");
const clearBtn = document.getElementById("clearBtn");

let isSending = false;
let activeScene = "tea";
const scenes = JSON.parse(document.getElementById("sceneData").textContent);
const stickers = JSON.parse(document.getElementById("stickerData").textContent);
const stickerTray = document.getElementById("stickerTray");
const stickerToggle = document.getElementById("stickerToggle");

function renderWelcome() {
    const scene = scenes[activeScene];
    chatArea.innerHTML = `<div class="welcome-msg"><div class="scene-eyebrow">${scene.eyebrow}</div><img class="scene-illustration" src="/static/art/${activeScene}.svg" alt="${scene.name}里的小熊陪伴你"/><h2>${scene.title}</h2><p>${scene.description}</p><div class="starter-list">${scene.starters.map(text => `<button type="button">${text}<span>↗</span></button>`).join("")}</div><div class="welcome-foot">一段对话，从此刻开始</div></div>`;
    chatArea.querySelectorAll('.starter-list button').forEach((button, index) => {
        button.addEventListener('click', () => {
            msgInput.value = scene.starters[index];
            msgInput.dispatchEvent(new Event('input'));
            msgInput.focus();
        });
    });
}

function setBusy(busy) {
    isSending = busy;
    sendBtn.disabled = busy;
    clearBtn.disabled = busy;
    document.querySelectorAll('[data-scene].scene-card, [data-sticker]').forEach(button => button.disabled = busy);
}

document.querySelectorAll('.scene-card').forEach(button => button.addEventListener('click', () => {
    if (isSending || activeScene === button.dataset.scene) return;
    activeScene = button.dataset.scene;
    document.querySelector('.app').dataset.scene = activeScene;
    document.getElementById('sceneName').textContent = scenes[activeScene].name;
    document.querySelectorAll('.scene-card').forEach(card => card.setAttribute('aria-pressed', String(card === button)));
    if (chatArea.querySelector('.welcome-msg')) renderWelcome();
    else {
        const notice = document.createElement('div');
        notice.className = 'scene-notice';
        notice.textContent = `已来到${scenes[activeScene].name} · 对话继续`;
        chatArea.appendChild(notice);
        chatArea.scrollTop = chatArea.scrollHeight;
    }
}));
stickerToggle.addEventListener('click', () => {
    stickerTray.hidden = !stickerTray.hidden;
    stickerToggle.setAttribute('aria-expanded', String(!stickerTray.hidden));
});
document.querySelectorAll('[data-sticker]').forEach(button => button.addEventListener('click', () => sendMessage(button.dataset.sticker)));
function appendSticker(id) {
    const bubble = appendMessage('user', '');
    bubble.classList.add('sticker-message');
    const img = document.createElement('img');
    img.src = `/static/art/${id === 'tea' ? 'sticker-tea' : id}.svg`;
    img.alt = stickers[id];
    bubble.append(img, document.createTextNode(stickers[id]));
}
renderWelcome();

// Configure markdown renderer
if (typeof marked !== 'undefined') {
    marked.setOptions({ breaks: true, gfm: true });
}

function renderMarkdown(text) {
    if (typeof marked === 'undefined' || typeof DOMPurify === 'undefined') {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    return DOMPurify.sanitize(marked.parse(text));
}

function renderLatex(element) {
    if (typeof renderMathInElement === 'undefined') return;
    renderMathInElement(element, {
        delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '$', right: '$', display: false },
            { left: '\\(', right: '\\)', display: false },
            { left: '\\[', right: '\\]', display: true },
        ],
        throwOnError: false,
    });
}

// Auto-resize textarea
msgInput.addEventListener("input", () => {
    msgInput.style.height = "auto";
    msgInput.style.height = Math.min(msgInput.scrollHeight, 120) + "px";
});

// Send on Enter (Shift+Enter for newline)
msgInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
        e.preventDefault();
        sendMessage();
    }
});

sendBtn.addEventListener("click", () => sendMessage());

function appendMessage(role, text) {
    // Remove welcome message if present
    const welcome = chatArea.querySelector(".welcome-msg");
    if (welcome) welcome.remove();

    const div = document.createElement("div");
    div.className = `message ${role}`;

    if (role === 'assistant') {
        div.innerHTML = renderMarkdown(text);
        chatArea.appendChild(div);
        renderLatex(div);
    } else {
        div.textContent = text;
        chatArea.appendChild(div);
    }

    chatArea.scrollTop = chatArea.scrollHeight;
    return div;
}

const BANNER_ICONS = {
    suggest: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    force: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    health: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78z"/></svg>',
};

function appendBanner(type, title, message) {
    const div = document.createElement("div");
    div.className = `banner ${type}`;
    const icon = BANNER_ICONS[type] || "";
    div.innerHTML = `<div class="banner-header">${icon}<div class="banner-title">${title}</div></div><div class="banner-body">${renderMarkdown(message)}</div>`;
    chatArea.appendChild(div);
    renderLatex(div.querySelector('.banner-body'));
    chatArea.scrollTop = chatArea.scrollHeight;
}

function showThinking(text) {
    removeThinking();
    const div = document.createElement("div");
    div.className = "thinking";
    div.id = "thinkingIndicator";
    div.innerHTML = `<div class="dots"><span></span><span></span><span></span></div> ${text}`;
    chatArea.appendChild(div);
    chatArea.scrollTop = chatArea.scrollHeight;
}

function removeThinking() {
    let el;
    while ((el = document.getElementById("thinkingIndicator"))) {
        el.remove();
    }
}

async function sendMessage(stickerId = null) {
    const text = stickerId ? "" : msgInput.value.trim();
    if ((!text && !stickerId) || isSending) return;

    setBusy(true);
    if (!stickerId) msgInput.value = "";
    msgInput.style.height = "auto";

    if (stickerId) appendSticker(stickerId);
    else appendMessage("user", text);
    stickerTray.hidden = true;
    stickerToggle.setAttribute('aria-expanded', 'false');
    showThinking("暖伴正在认真听你说...");

    try {
        const resp = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text, scene: activeScene, sticker: stickerId }),
        });

        if (!resp.ok) {
            const error = await resp.json();
            throw new Error(error.error || "消息发送失败，请稍后重试");
        }
        removeThinking();

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (!done) {
                buffer += decoder.decode(value, { stream: true });
            }

            // Parse SSE events from buffer
            const parts = buffer.split("\n\n");
            buffer = parts.pop(); // Keep incomplete part

            for (const part of parts) {
                if (!part.trim()) continue;
                let eventType = "message";
                let data = "";

                for (const line of part.split("\n")) {
                    if (line.startsWith("event: ")) {
                        eventType = line.slice(7);
                    } else if (line.startsWith("data: ")) {
                        data = line.slice(6);
                    }
                }

                if (!data) continue;

                try {
                    const parsed = JSON.parse(data);
                    handleSSEEvent(eventType, parsed);
                } catch (e) {
                    // ignore parse errors
                }
            }

            if (done) break;
        }
    } catch (err) {
        removeThinking();
        appendMessage("assistant", "连接错误：" + err.message);
    }

    setBusy(false);
    msgInput.focus();
}

function handleSSEEvent(type, data) {
    switch (type) {
        case "assistant_message":
            appendMessage("assistant", data.text);
            break;
        case "thinking":
            showThinking(data.status);
            break;
        case "intervention":
            removeThinking();
            if (data.type === "force") {
                appendBanner("force", "!! 紧急心理干预通知", data.message);
            } else {
                appendBanner("suggest", "心理健康提醒", data.message);
            }
            break;
        case "health_advice":
            removeThinking();
            appendBanner("health", "健康建议", data.message);
            break;
        case "error":
            removeThinking();
            appendMessage("assistant", "错误：" + data.text);
            break;
        case "done":
            removeThinking();
            break;
    }
}

// Settings
settingsBtn.addEventListener("click", () => {
    settingsModal.classList.remove("hidden");
    loadConfig();
});

closeSettings.addEventListener("click", () => {
    settingsModal.classList.add("hidden");
});

settingsModal.addEventListener("click", (e) => {
    if (e.target === settingsModal) {
        settingsModal.classList.add("hidden");
    }
});

async function loadConfig() {
    try {
        const resp = await fetch("/api/config");
        const cfg = await resp.json();
        // Populate fields (show masked key as placeholder)
        document.getElementById("a_api_base").value = cfg.model_a.api_base;
        document.getElementById("a_api_key").value = "";
        document.getElementById("a_api_key").placeholder = cfg.model_a.api_key;
        document.getElementById("a_model").value = cfg.model_a.model;
        document.getElementById("b_api_base").value = cfg.model_b.api_base;
        document.getElementById("b_api_key").value = "";
        document.getElementById("b_api_key").placeholder = cfg.model_b.api_key;
        document.getElementById("b_model").value = cfg.model_b.model;
        document.getElementById("c_api_base").value = cfg.model_c.api_base;
        document.getElementById("c_api_key").value = "";
        document.getElementById("c_api_key").placeholder = cfg.model_c.api_key;
        document.getElementById("c_model").value = cfg.model_c.model;
    } catch (e) {
        // ignore
    }
}

saveSettings.addEventListener("click", async () => {
    const cfg = {
        model_a: {
            api_base: document.getElementById("a_api_base").value || undefined,
            api_key: document.getElementById("a_api_key").value || undefined,
            model: document.getElementById("a_model").value || undefined,
        },
        model_b: {
            api_base: document.getElementById("b_api_base").value || undefined,
            api_key: document.getElementById("b_api_key").value || undefined,
            model: document.getElementById("b_model").value || undefined,
        },
        model_c: {
            api_base: document.getElementById("c_api_base").value || undefined,
            api_key: document.getElementById("c_api_key").value || undefined,
            model: document.getElementById("c_model").value || undefined,
        },
    };

    try {
        await fetch("/api/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(cfg),
        });
        settingsModal.classList.add("hidden");
    } catch (e) {
        alert("保存失败：" + e.message);
    }
});

resetDefaults.addEventListener("click", async () => {
    // Clear all input fields and reset selects
    document.querySelectorAll(".config-section input").forEach((input) => {
        input.value = "";
    });
    document.querySelectorAll(".config-section select").forEach((select) => {
        select.selectedIndex = 0;
    });
    // Post empty config to reset to defaults
    try {
        await fetch("/api/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ reset: true }),
        });
        await loadConfig();
    } catch (e) {
        alert("恢复默认失败：" + e.message);
    }
});

// Clear keeps the selected scene, and waits for server confirmation.
clearBtn.addEventListener("click", async () => {
    if (isSending) return;
    setBusy(true);
    try {
        const response = await fetch("/api/clear", { method: "POST" });
        if (!response.ok) throw new Error("清空失败，请稍后再试");
        renderWelcome();
    } catch (e) {
        alert(e.message);
    } finally {
        setBusy(false);
    }
});

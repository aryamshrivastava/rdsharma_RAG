const API = window.location.origin;

const chat = document.getElementById("chat");
const form = document.getElementById("textForm");
const q = document.getElementById("q");
const explain = document.getElementById("explain");
const fastMode = document.getElementById("fastMode");
const cancelReqBtn = document.getElementById("cancelReq");

const sendBtn = document.getElementById("sendBtn");
const sendImgBtn = document.getElementById("sendImg");
const imgInput = document.getElementById("img");
const uploadBtn = document.getElementById("uploadBtn");
const imagePreviewContainer = document.getElementById("imagePreviewContainer");
const imagePreview = document.getElementById("imagePreview");
const clearImageBtn = document.getElementById("clearImageBtn");
const imageContext = document.getElementById("imageContext");
const uploaderBtn = document.getElementById("uploaderBtn");

let emptyState = document.getElementById("emptyState");
const msgCount = document.getElementById("msgCount");
const toast = document.getElementById("toast");
const clearChatBtn = document.getElementById("clearChat");
const chips = document.getElementById("chips");
const fileName = document.getElementById("fileName");

let count = 0;
let typingEl = null;
let isBusy = false;
let activeController = null;
let timerId = null;
let startTs = 0;

const cache = new Map();

// Conversation history tracking
let conversationHistory = [];
const STORAGE_KEY = "rd_sharma_conversation_history";

// Load conversation history from local storage
function loadConversationHistory() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      conversationHistory = JSON.parse(stored);
      if (conversationHistory.length > 0) {
        conversationHistory.forEach(entry => {
          if (entry.type === "question") {
            addMsg(entry.content, "me");
          } else if (entry.type === "method") {
            addMethodBadge(entry.method);
          } else if (entry.type === "answer") {
            addMsg(entry.content, "bot");
          }
        });
      }
    }
  } catch (e) {
    console.warn("Could not load conversation history", e);
  }
}

// Save conversation entry
function saveConversationEntry(type, content, method = null) {
  const entry = {
    type,
    content,
    timestamp: new Date().toISOString(),
    method: method
  };
  conversationHistory.push(entry);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversationHistory));
  } catch (e) {
    console.warn("Could not save conversation history", e);
  }
}

// Add method badge to display
function addMethodBadge(method) {
  const badge = document.createElement("div");
  badge.className = "method-badge";
  badge.style.cssText = `
    background: linear-gradient(135deg, rgba(45, 107, 255, 0.2), rgba(102, 153, 255, 0.2));
    border: 1px solid rgba(45, 107, 255, 0.4);
    border-radius: 20px;
    padding: 6px 14px;
    margin: 8px 0;
    display: inline-block;
    font-size: 12px;
    font-weight: 500;
    color: var(--blue-text, #2d6bff);
  `;
  badge.textContent = `📌 Method: ${method}`;
  chat.appendChild(badge);
  scrollToBottom();
}

const TIMEOUT_MS_TEXT = 120000;
const TIMEOUT_MS_IMAGE = 90000;

/* ---------- Utilities ---------- */

function nowTime() {
  const d = new Date();
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function setToast(text, type = "info") {
  toast.textContent = text || "";
  toast.style.color =
    type === "error" ? "rgba(255,77,109,.92)"
      : type === "success" ? "rgba(60,255,179,.92)"
        : "rgba(234,240,255,.86)";
  if (text) setTimeout(() => toast.textContent === text && (toast.textContent = ""), 2800);
}

function updateCount() {
  msgCount.textContent = `${count} message${count === 1 ? "" : "s"}`;
}

function ensureNotEmpty() {
  if (count > 0 && emptyState) emptyState.style.display = "none";
}

function scrollToBottom() {
  chat.scrollTop = chat.scrollHeight;
}

function convertMarkdownImagesToHTML(text) {
  // Convert markdown images ![alt](url) to HTML img tags
  // IMPORTANT: Extract images BEFORE escaping HTML to preserve base64 data URLs

  const imageRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
  let images = [];
  let imageIndex = 0;

  // Step 1: Extract and replace images with placeholders
  text = text.replace(imageRegex, (match, alt, url) => {
    images.push({ alt, url });
    return `__IMAGE_PLACEHOLDER_${imageIndex++}__`;
  });

  // Step 2: Escape remaining HTML
  let html = text.replace(/</g, "&lt;").replace(/>/g, "&gt;");

  // Step 3: Convert line breaks
  html = html.replace(/\n/g, "<br>");

  // Step 4: Replace image placeholders with actual img tags
  images.forEach((img, idx) => {
    const imgTag = `<img src="${img.url}" alt="${img.alt}" style="max-width:100%; max-height:600px; border-radius:8px; margin:16px 0; border:1px solid #ddd;" />`;
    html = html.replace(`__IMAGE_PLACEHOLDER_${idx}__`, imgTag);
  });

  return html;
}

function addMsg(text, who) {
  ensureNotEmpty();

  const row = document.createElement("div");
  row.className = `msg ${who}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = who === "me" ? "You" : "AI";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  // For bot messages, render markdown images as actual img tags
  if (who === "bot") {
    bubble.innerHTML = convertMarkdownImagesToHTML(text);
  } else {
    bubble.textContent = text;
  }

  const meta = document.createElement("div");
  meta.className = "meta-row";
  meta.innerHTML = `<span>${who === "me" ? "Sent" : "Answer"}</span><span>${nowTime()}</span>`;

  bubble.appendChild(meta);

  who === "me"
    ? (row.appendChild(bubble), row.appendChild(avatar))
    : (row.appendChild(avatar), row.appendChild(bubble));

  chat.appendChild(row);
  count++;
  updateCount();
  scrollToBottom();
}

function showTyping(text = "Thinking…") {
  if (typingEl) return;

  typingEl = document.createElement("div");
  typingEl.className = "typing";
  typingEl.innerHTML = `
    <div class="avatar">AI</div>
    <div class="dots">
      <span></span><span></span><span></span>
      <div id="statusLine" style="font-size:12px;margin-top:8px;">${text}</div>
      <div id="timerLine" style="font-size:11px;opacity:.6;">0s</div>
    </div>`;
  chat.appendChild(typingEl);
  scrollToBottom();

  startTs = Date.now();
  timerId = setInterval(() => {
    const s = Math.floor((Date.now() - startTs) / 1000);
    const el = document.getElementById("timerLine");
    if (el) el.textContent = `${s}s`;
  }, 500);
}

function hideTyping() {
  typingEl?.remove();
  typingEl = null;
  clearInterval(timerId);
  timerId = null;
}

function setBusyState(busy) {
  isBusy = busy;
  sendBtn.disabled = busy;
  sendImgBtn.disabled = busy;
}

async function fetchWithTimeout(url, options, timeoutMs) {
  if (activeController) activeController.abort();

  const controller = new AbortController();
  activeController = controller;

  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(id);
  }
}

/* ---------- Input UX ---------- */

function autoGrow() {
  q.style.height = "auto";
  q.style.height = Math.min(q.scrollHeight, 180) + "px";
}
q.addEventListener("input", autoGrow);

q.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});

/* ---------- Text Query ---------- */

let selectedMethod = null;
let pendingQuestion = null;

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (isBusy) return;

  const text = q.value.trim();
  if (!text) return;

  // Store question and get methods
  pendingQuestion = text;
  addMsg(text, "me");
  saveConversationEntry("question", text);
  q.value = "";
  autoGrow();

  setBusyState(true);
  showTyping("Available solution methods...");

  try {
    // Get available methods
    const fd = new FormData();
    fd.append("question", text);

    const methodRes = await fetchWithTimeout(`${API}/chat/methods`, {
      method: "POST",
      body: fd
    }, 30000);

    const methodData = await methodRes.json();
    hideTyping();

    if (methodData.error || !methodData.methods || methodData.methods.length === 0) {
      // No methods returned, proceed with default
      selectedMethod = null;
      await submitAnswer(text, null);
      return;
    }

    // Show method selection
    showMethodSelection(methodData.methods);

  } catch (err) {
    hideTyping();
    // On error, just proceed without method selection
    selectedMethod = null;
    await submitAnswer(text, null);
  }
});

function showMethodSelection(methods) {
  setBusyState(false);

  // Create method selection UI
  const methodDiv = document.createElement("div");
  methodDiv.className = "method-selection";
  methodDiv.style.cssText = `
    background: rgba(45, 107, 255, 0.1);
    border: 1px solid rgba(45, 107, 255, 0.3);
    border-radius: 12px;
    padding: 16px;
    margin: 12px 0;
    animation: slideUp 0.3s ease;
  `;

  const title = document.createElement("div");
  title.style.cssText = `
    font-weight: 500;
    margin-bottom: 12px;
    color: var(--text);
    font-size: 14px;
  `;
  title.textContent = "Choose a solution method:";
  methodDiv.appendChild(title);

  const buttonsDiv = document.createElement("div");
  buttonsDiv.style.cssText = `
    display: flex;
    flex-direction: column;
    gap: 8px;
  `;

  methods.forEach((method, idx) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn method-btn";
    btn.style.cssText = `
      background: rgba(45, 107, 255, 0.2);
      border: 1px solid var(--blue);
      color: var(--text);
      padding: 10px 12px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 13px;
      text-align: left;
      transition: all 0.2s;
    `;
    btn.textContent = method;

    btn.onmouseover = () => {
      btn.style.background = "rgba(45, 107, 255, 0.35)";
    };
    btn.onmouseout = () => {
      btn.style.background = "rgba(45, 107, 255, 0.2)";
    };

    btn.onclick = async () => {
      selectedMethod = method;
      methodDiv.remove();
      addMethodBadge(method);
      saveConversationEntry("method", null, method);
      setBusyState(true);
      showTyping("Generating solution…");

      // Determine if this is from text or image
      if (pendingImageData) {
        await submitImageAnswer(method);
      } else {
        await submitAnswer(pendingQuestion, selectedMethod);
      }
    };

    buttonsDiv.appendChild(btn);
  });

  methodDiv.appendChild(buttonsDiv);
  chat.appendChild(methodDiv);
  scrollToBottom();
}

async function submitAnswer(question, method) {
  // 🔒 Safety: fast mode disables step-by-step
  let wantExplain = explain.checked;
  if (fastMode.checked && wantExplain) {
    wantExplain = false;
    explain.checked = false;
    setToast("Fast mode → step-by-step disabled for speed", "info");
  }

  const cacheKey = `${wantExplain ? "explain" : "book"}|${question}|${method || "default"}`;
  if (cache.has(cacheKey)) {
    hideTyping();
    addMsg(cache.get(cacheKey), "bot");
    setBusyState(false);
    return;
  }

  try {
    const fd = new FormData();
    fd.append("question", question);
    fd.append("explain", wantExplain ? "true" : "false");
    if (method) fd.append("method", method);

    const res = await fetchWithTimeout(`${API}/chat/text`, {
      method: "POST",
      body: fd
    }, TIMEOUT_MS_TEXT);

    const data = await res.json();
    hideTyping();

    if (!res.ok) {
      addMsg(`Server error (${res.status})`, "bot");
      setBusyState(false);
      return;
    }

    const answerText = data.answer || "No answer";
    addMsg(answerText, "bot");
    saveConversationEntry("answer", answerText, selectedMethod);
    cache.set(cacheKey, answerText);

  } catch (err) {
    hideTyping();
    addMsg(
      err.name === "AbortError"
        ? "Request timed out. Try again or keep step-by-step off."
        : "Network error. Is the backend running?",
      "bot"
    );
  } finally {
    setBusyState(false);
  }
}

/* ---------- Image Preview & Context ---------- */

// Setup upload button with retry logic
function setupUploadButton() {
  const btn = document.querySelector("#uploadBtn");
  const input = document.querySelector("#img");

  if (!btn || !input) {
    console.warn("Upload elements not found, retrying in 100ms");
    setTimeout(setupUploadButton, 100);
    return;
  }

  // Remove any existing listeners
  btn.onclick = null;
  btn.removeEventListener("click", handleUploadClick);

  // Add fresh listener
  btn.addEventListener("click", handleUploadClick);
  console.log("✓ Upload button is now functional");
}

function handleUploadClick(e) {
  e.preventDefault();
  e.stopPropagation();
  const input = document.querySelector("#img");
  if (input) input.click();
}

// Setup immediately
setupUploadButton();

// Handle file selection
const fileInputElement = document.querySelector("#img");
if (fileInputElement) {
  fileInputElement.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const previewContainer = document.querySelector("#imagePreviewContainer");
      const uploaderDiv = document.querySelector("#uploaderBtn");
      const previewImg = document.querySelector("#imagePreview");
      const contextArea = document.querySelector("#imageContext");

      if (previewContainer) previewContainer.style.display = "flex";
      if (uploaderDiv) uploaderDiv.style.display = "none";
      if (previewImg) previewImg.src = event.target.result;
      if (previewImg) previewImg.alt = file.name;
      if (contextArea) {
        contextArea.value = "";
        contextArea.focus();
      }
    };

    reader.readAsDataURL(file);
  });
}

// Clear image button
const clearBtn = document.querySelector("#clearImageBtn");
if (clearBtn) {
  clearBtn.addEventListener("click", (e) => {
    e.preventDefault();
    const input = document.querySelector("#img");
    const previewContainer = document.querySelector("#imagePreviewContainer");
    const uploaderDiv = document.querySelector("#uploaderBtn");
    const contextArea = document.querySelector("#imageContext");

    if (input) input.value = "";
    if (previewContainer) previewContainer.style.display = "none";
    if (uploaderDiv) uploaderDiv.style.display = "flex";
    if (contextArea) contextArea.value = "";
  });
}

// Image context keydown
imageContext.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendImgBtn.click();
  }
});

// Clear chat button
clearChatBtn.addEventListener("click", () => {
  chat.innerHTML = "";
  count = 0;
  conversationHistory = [];
  localStorage.removeItem(STORAGE_KEY);
  updateCount();
  emptyState.style.display = "block";
  setToast("Chat cleared", "success");
});

// Send image button
let pendingImageData = null;

const sendImgBtnElement = document.querySelector("#sendImg");
if (sendImgBtnElement) {
  sendImgBtnElement.addEventListener("click", async () => {
    if (isBusy) return;

    const fileInput = document.querySelector("#img");
    const contextArea = document.querySelector("#imageContext");
    const file = fileInput?.files[0];

    if (!file) return setToast("Choose an image first.", "error");

    const context = (contextArea?.value || "").trim();
    addMsg(`[Image: ${file.name}${context ? " - " + context : ""}]`, "me");
    saveConversationEntry("question", `[Image: ${file.name}${context ? " - " + context : ""}]`);

    setBusyState(true);
    showTyping("Reading image…");

    try {
      const fd = new FormData();
      fd.append("file", file);
      if (context) fd.append("context", context);

      // Step 1: Extract text from image
      const res = await fetchWithTimeout(`${API}/chat/image/extract`, {
        method: "POST",
        body: fd
      }, TIMEOUT_MS_IMAGE);

      const data = await res.json();
      hideTyping();

      if (!res.ok) {
        addMsg(`Server error (${res.status}): ${data.message || "Unknown error"}`, "bot");
        return;
      }

      if (data.error) {
        addMsg(data.message || "Error processing image", "bot");
        return;
      }

      // Show extracted question
      addMsg(`📷 Extracted: ${data.extracted_question}`, "bot");
      saveConversationEntry("extracted_question", data.extracted_question);

      // Store the pending image data for later use
      pendingImageData = {
        question: data.extracted_question,
        diagramDescription: data.diagram_description,
        sessionId: data.session_id
      };

      // Step 2: Show method selection
      showMethodSelection(data.methods);

    } catch (err) {
      hideTyping();
      addMsg("Image request timed out or failed.", "bot");
    } finally {
      setBusyState(false);
    }
  });
}

async function submitImageAnswer(method) {
  if (!pendingImageData) return;

  const { question, diagramDescription, sessionId } = pendingImageData;

  setBusyState(true);
  showTyping("Generating solution…");

  try {
    const fd = new FormData();
    fd.append("question", question);
    fd.append("session_id", sessionId);
    if (method) fd.append("method", method);
    if (diagramDescription) fd.append("diagram_description", diagramDescription);

    const res = await fetchWithTimeout(`${API}/chat/image/answer`, {
      method: "POST",
      body: fd
    }, TIMEOUT_MS_IMAGE);

    const data = await res.json();
    hideTyping();

    if (!res.ok) {
      addMsg(`Server error (${res.status}): ${data.answer || "Unknown error"}`, "bot");
      return;
    }

    if (data.error) {
      addMsg(data.answer || "Error generating answer", "bot");
      return;
    }

    const answerText = data.answer || "No answer";
    addMsg(answerText, "bot");
    saveConversationEntry("answer", answerText, method);

    // Clear image upload UI
    const fileInput = document.querySelector("#img");
    const previewContainer = document.querySelector("#imagePreviewContainer");
    const uploaderDiv = document.querySelector("#uploaderBtn");
    const contextArea = document.querySelector("#imageContext");
    if (fileInput) fileInput.value = "";
    if (previewContainer) previewContainer.style.display = "none";
    if (uploaderDiv) uploaderDiv.style.display = "flex";
    if (contextArea) contextArea.value = "";

    pendingImageData = null;

  } catch (err) {
    hideTyping();
    addMsg("Answer generation timed out or failed.", "bot");
  } finally {
    setBusyState(false);
  }
}

/* ---------- Init ---------- */

updateCount();
autoGrow();
loadConversationHistory();

'use strict';

const ACCESS_KEY_STORAGE = 'llm_chat_access_key';
const AUTH_PAGE  = '/auth';
const CHAT_PAGE  = '/';
const MAX_LENGTH = 500;
const ACCESS_KEY_MIN = 8;
const ACCESS_KEY_MAX = 255;
const ACCESS_KEY_PATTERN = /^[A-Za-z0-9_-]{8,255}$/;

function getAccessKey()    { return localStorage.getItem(ACCESS_KEY_STORAGE); }
function setAccessKey(key) { localStorage.setItem(ACCESS_KEY_STORAGE, key); }
function clearAccessKey()  { localStorage.removeItem(ACCESS_KEY_STORAGE); }

function buildHeaders(extra) {
  return Object.assign(
    { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + getAccessKey() },
    extra || {}
  );
}

async function apiFetch(path, options) {
  options = options || {};
  const res = await fetch(path, Object.assign({}, options, { headers: buildHeaders(options.headers) }));

  if (res.status === 403) {
    clearAccessKey();
    window.location.href = AUTH_PAGE;
    throw new Error('Unauthorized');
  }

  return res;
}

const bodyClasses = document.body.classList;

if (bodyClasses.contains('auth')) {
  initAuthPage();
} else if (bodyClasses.contains('chat')) {
  initChatPage();
}

function initAuthPage() {
  if (getAccessKey()) {
    window.location.href = CHAT_PAGE;
    return;
  }

  const form    = document.querySelector('.auth-form');
  const input   = document.getElementById('access-key');
  const button  = document.querySelector('.auth-form__button');
  const errorEl = document.querySelector('.auth-form__error');

  var isSubmitting = false;

  function validateAccessKey(value) {
    var trimmed = value.trim();

    if (!trimmed) {
      return { isValid: false, message: '' };
    }

    if (trimmed.length < ACCESS_KEY_MIN || trimmed.length > ACCESS_KEY_MAX) {
      return { isValid: false, message: 'Access key must be 8–255 characters long.' };
    }

    if (!ACCESS_KEY_PATTERN.test(trimmed)) {
      return { isValid: false, message: 'Access key can include letters, numbers, hyphen, underscore only.' };
    }

    return { isValid: true, value: trimmed, message: '' };
  }

  function updateAuthButton(showValidationError) {
    var result = validateAccessKey(input.value);
    button.disabled = isSubmitting || !result.isValid;

    if (showValidationError) {
      errorEl.textContent = result.message || '';
    }
  }

  input.addEventListener('input', function () {
    var result = validateAccessKey(input.value);
    if (result.isValid) {
      errorEl.textContent = '';
    }
    updateAuthButton(false);
  });

  updateAuthButton(false);

  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    var result = validateAccessKey(input.value);
    if (!result.isValid) {
      errorEl.textContent = result.message || 'Invalid access key.';
      updateAuthButton(true);
      return;
    }

    const key = result.value;

    isSubmitting      = true;
    updateAuthButton(false);
    button.textContent  = 'Authenticating…';
    errorEl.textContent = '';

    try {
      const res = await fetch('/api/me', {
        headers: { 'Authorization': 'Bearer ' + key }
      });

      if (res.ok) {
        setAccessKey(key);
        window.location.href = CHAT_PAGE;
      } else {
        var data = {};
        try { data = await res.json(); } catch (_) {}
        errorEl.textContent = data.detail || 'Invalid access key. Please try again.';
      }
    } catch (_) {
      errorEl.textContent = 'Network error. Please check your connection and try again.';
    } finally {
      isSubmitting      = false;
      updateAuthButton(false);
      button.textContent = 'Authenticate';
    }
  });
}

function initChatPage() {
  if (!getAccessKey()) {
    window.location.href = AUTH_PAGE;
    return;
  }

  const messagesEl  = document.querySelector('.chat__messages');
  const form        = document.querySelector('.chat__input-form');
  const input       = document.querySelector('.chat__input');
  const sendBtn     = document.querySelector('.chat__send-button');
  const titleEl     = document.querySelector('.chat__title');
  const logoutBtn   = document.querySelector('.chat__logout-button');
  const charCountEl = document.querySelector('.chat__char-count');

  var isWaiting = false;

  logoutBtn.addEventListener('click', function () {
    clearAccessKey();
    window.location.href = AUTH_PAGE;
  });

  function formatTimestamp(dateStr) {
    if (!dateStr) return '';
    var d = new Date(dateStr);
    if (isNaN(d.getTime())) return '';
    function pad(n) { return String(n).padStart(2, '0'); }
    return pad(d.getDate()) + '.' + pad(d.getMonth() + 1) + '.' + d.getFullYear()
         + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
  }

  function updateSendButton() {
    var len        = input.value.length;
    var trimmedLen = input.value.trim().length;

    charCountEl.textContent = len + ' / ' + MAX_LENGTH;
    charCountEl.classList.remove('chat__char-count--warning', 'chat__char-count--over');

    if (len >= MAX_LENGTH) {
      charCountEl.classList.add('chat__char-count--over');
    } else if (len >= Math.floor(MAX_LENGTH * 0.8)) {
      charCountEl.classList.add('chat__char-count--warning');
    }

    sendBtn.disabled = isWaiting || trimmedLen === 0;
  }

  input.addEventListener('input', updateSendButton);

  function appendMessage(content, isResponse, timestamp) {
    const wrap = document.createElement('div');
    wrap.className = 'chat-message ' + (isResponse ? 'chat-message--response' : 'chat-message--user');

    const inner = document.createElement('div');
    inner.className = 'chat-message__inner';

    const bubble = document.createElement('div');
    bubble.className   = 'chat-message__bubble';
    bubble.textContent = content;

    const time = document.createElement('time');
    time.className   = 'chat-message__time';
    time.textContent = formatTimestamp(timestamp);
    if (timestamp) time.dateTime = timestamp;

    inner.appendChild(bubble);
    inner.appendChild(time);
    wrap.appendChild(inner);
    messagesEl.appendChild(wrap);
    scrollToBottom();
    return wrap;
  }

  function showTypingIndicator() {
    const wrap = document.createElement('div');
    wrap.className = 'chat-message chat-message--response chat-message--typing';

    const inner = document.createElement('div');
    inner.className = 'chat-message__inner';

    const bubble = document.createElement('div');
    bubble.className = 'chat-message__bubble';
    bubble.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';

    inner.appendChild(bubble);
    wrap.appendChild(inner);
    messagesEl.appendChild(wrap);
    scrollToBottom();
    return wrap;
  }

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function setInputEnabled(enabled) {
    isWaiting      = !enabled;
    input.disabled = !enabled;
    updateSendButton();
  }

  async function loadUser() {
    try {
      const res  = await apiFetch('/api/me');
      const user = await res.json();
      titleEl.textContent = 'Neural Oracle 🔮 — ' + user.name;
    } catch (_) {
    }
  }

  async function loadHistory() {
    try {
      const res = await apiFetch('/api/chat');

      if (!res.ok) {
        showEmptyState('⚠️ Failed to load chat history (server error ' + res.status + ').');
        return;
      }

      const data = await res.json();
      messagesEl.innerHTML = '';

      const messages = data.content || [];
      if (messages.length === 0) {
        showEmptyState();
      } else {
        messages.forEach(function (msg) {
          appendMessage(msg.content, msg.is_response, msg.created_at);
        });
      }
    } catch (err) {
      if (getAccessKey()) {
        showEmptyState('⚠️ Could not load chat history. Please refresh the page.');
        console.error('loadHistory error:', err);
      }
    }
  }

  function showEmptyState(message) {
    const empty = document.createElement('p');
    empty.className   = 'chat__empty';
    empty.textContent = message || 'No messages yet. Say hello!';
    messagesEl.appendChild(empty);
  }

  async function sendMessage(content) {
    const emptyEl = messagesEl.querySelector('.chat__empty');
    if (emptyEl) emptyEl.remove();

    const sentAt = new Date().toISOString();
    appendMessage(content, false, sentAt);
    setInputEnabled(false);

    const typing = showTypingIndicator();

    try {
      const res = await apiFetch('/api/chat', {
        method: 'POST',
        body: JSON.stringify({
          content:     content,
          is_response: false,
          created_at:  null,
          user_id:     null
        })
      });

      typing.remove();

      if (!res.ok) {
        appendMessage('⚠️ Failed to get a response. Please try again.', true, new Date().toISOString());
        return;
      }

      const reply = await res.json();
      appendMessage(reply.content, true, reply.created_at);
    } catch (_) {
      typing.remove();
      if (getAccessKey()) {
        appendMessage('⚠️ Network error. Please try again.', true, new Date().toISOString());
      }
    } finally {
      setInputEnabled(true);
      input.focus();
    }
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();

    const content = input.value.trim();

    if (!content || content.length > MAX_LENGTH) return;

    input.value = '';
    updateSendButton();
    sendMessage(content);
  });

  updateSendButton();
  loadUser();
  loadHistory();
}

const form = document.querySelector('#chat-form');
const prompt = document.querySelector('#prompt');
const messages = document.querySelector('#messages');
const send = document.querySelector('#send');
const newChat = document.querySelector('#new-chat');
let userId = localStorage.getItem('microchat-user-id');
if (!userId) { userId = 'u-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 12); localStorage.setItem('microchat-user-id', userId); }
function addMessage(role, text, extraClass = '') { const item = document.createElement('article'); item.className = `message ${role} ${extraClass}`; const avatar = document.createElement('div'); avatar.className = 'avatar'; avatar.textContent = role === 'assistant' ? '✦' : 'Você'; const bubble = document.createElement('div'); bubble.className = 'bubble'; bubble.textContent = text; item.append(avatar, bubble); messages.appendChild(item); messages.scrollTop = messages.scrollHeight; return item; }
function resize() { prompt.style.height = 'auto'; prompt.style.height = Math.min(prompt.scrollHeight, 150) + 'px'; }
prompt.addEventListener('input', resize);
prompt.addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); } });
form.addEventListener('submit', async event => { event.preventDefault(); const text = prompt.value.trim(); if (!text || send.disabled) return; addMessage('user', text); prompt.value = ''; resize(); send.disabled = true; const loading = addMessage('assistant', 'Pensando...', 'typing'); try { const response = await fetch('/api/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ user_id: userId, prompt: text }) }); const data = await response.json(); loading.remove(); if (!response.ok) throw new Error(data.error || 'Erro ao enviar a mensagem'); addMessage('assistant', data.response); } catch (error) { loading.remove(); addMessage('assistant', `Não consegui responder agora: ${error.message}`); } finally { send.disabled = false; prompt.focus(); } });
newChat.addEventListener('click', async () => { try { await fetch('/api/reset', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({user_id: userId}) }); } catch (_) {} messages.innerHTML = ''; addMessage('assistant', 'Conversa nova iniciada. O que vamos fazer?'); prompt.focus(); });

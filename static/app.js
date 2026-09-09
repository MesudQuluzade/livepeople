const loadStyle = (href) => {
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = href;
    document.head.appendChild(link);
  }
};

loadStyle('/static/social.css');

document.querySelectorAll('.toast').forEach((item) => {
  setTimeout(() => item.remove(), 3500);
});

if (document.querySelector('.admin-menu') || document.querySelector('.admin-profile-page')) {
  loadStyle('/static/admin.css');
  loadStyle('/static/admin-profile.css');
}

if (document.querySelector('.coin-hero') || document.querySelector('.coin-packages')) {
  loadStyle('/static/coins-extra.css');
}

if (location.pathname === '/chat/' && document.querySelector('.messages')) {
  const conversationId = new URLSearchParams(location.search).get('conversation');
  if (conversationId) {
    const box = document.querySelector('.messages');
    const poll = () => fetch('/chat/messages/' + conversationId + '/')
      .then((response) => response.json())
      .then((data) => {
        if (data.messages.length > box.children.length) {
          data.messages.slice(box.children.length).forEach((message) => {
            const bubble = document.createElement('div');
            bubble.className = 'bubble';
            bubble.textContent = message.body;
            const time = document.createElement('small');
            time.textContent = message.time;
            bubble.appendChild(time);
            box.appendChild(bubble);
          });
          box.scrollTop = box.scrollHeight;
        }
      })
      .catch(() => {});
    setInterval(poll, 3000);
  }
}

if (window.lucide) window.lucide.createIcons();

loadStyle('/static/modern.css');

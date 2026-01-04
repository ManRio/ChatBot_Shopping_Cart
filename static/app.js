(function () {
  // -----------------------
  // 1) MODAL CARRITO
  // -----------------------
  const cartBtn = document.getElementById('cart-button');
  const cartModal = document.getElementById('cart-modal');
  const cartPanel = document.getElementById('cart-panel');
  const cartCloseX = document.getElementById('cart-close');
  const cartCloseFooter = document.getElementById('cart-close-footer');

  function openCart() {
    if (!cartModal || !cartBtn || !cartPanel) return;

    cartModal.classList.remove('is-hidden');
    cartBtn.setAttribute('aria-expanded', 'true');
    document.body.classList.add('no-scroll');

    // Posicionar bajo el botón del carrito
    const rect = cartBtn.getBoundingClientRect();
    const top = rect.bottom + window.scrollY + 10;
    const left = rect.left + window.scrollX;

    const panelWidth = cartPanel.offsetWidth || 520;
    const viewportRight = window.scrollX + window.innerWidth;

    let computedLeft = left;
    if (left + panelWidth > viewportRight - 18) {
      computedLeft = Math.max(18, viewportRight - panelWidth - 18);
    }

    cartPanel.style.top = `${top}px`;
    cartPanel.style.left = `${computedLeft}px`;
  }

  function closeCart() {
    if (!cartModal || !cartBtn) return;
    cartModal.classList.add('is-hidden');
    cartBtn.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('no-scroll');
  }

  cartBtn?.addEventListener('click', openCart);
  cartCloseX?.addEventListener('click', closeCart);
  cartCloseFooter?.addEventListener('click', closeCart);

  cartModal?.addEventListener('click', (e) => {
    const target = e.target;
    if (
      target &&
      target.getAttribute &&
      target.getAttribute('data-close') === 'true'
    ) {
      closeCart();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (
      e.key === 'Escape' &&
      cartModal &&
      !cartModal.classList.contains('is-hidden')
    ) {
      closeCart();
    }
  });

  // -----------------------
  // 2) CHAT WIDGET
  // -----------------------
  const chatFab = document.getElementById('chat-fab');
  const chatWidget = document.getElementById('chat-widget');
  const chatClose = document.getElementById('chat-close');
  const chatMessages = document.getElementById('chat-messages');

  function scrollChatToBottom() {
    if (!chatMessages) return;
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function openChat() {
    if (!chatWidget || !chatFab) return;
    chatWidget.classList.remove('is-collapsed');
    chatFab.setAttribute('aria-expanded', 'true');
    scrollChatToBottom();
  }

  function closeChat() {
    if (!chatWidget || !chatFab) return;
    chatWidget.classList.add('is-collapsed');
    chatFab.setAttribute('aria-expanded', 'false');
  }

  // Estado inicial: abierto siempre
  scrollChatToBottom();

  // El botón "Chat" solo abre si estaba cerrado (NO cierra)
  chatFab?.addEventListener('click', () => {
    if (chatWidget && chatWidget.classList.contains('is-collapsed')) openChat();
  });

  // Solo se cierra con la X
  chatClose?.addEventListener('click', closeChat);

  // -----------------------
  // 3) MODAL PRODUCTO
  // -----------------------
  const productModal = document.getElementById('product-modal');
  const productPanel = document.getElementById('product-panel');
  const productCloseX = document.getElementById('product-close');
  const productCloseFooter = document.getElementById('product-close-footer');

  const productTitle = document.getElementById('product-modal-title');
  const productImg = document.getElementById('product-modal-img');
  const productPrice = document.getElementById('product-modal-price');
  const productDesc = document.getElementById('product-modal-desc');
  const productAddForm = document.getElementById('product-add-form');

  function openProductFromCard(card) {
    if (
      !productModal ||
      !productTitle ||
      !productImg ||
      !productPrice ||
      !productDesc ||
      !productAddForm
    )
      return;

    const id = card.getAttribute('data-product-id');
    const name = card.getAttribute('data-product-name');
    const price = card.getAttribute('data-product-price');
    const desc = card.getAttribute('data-product-desc');
    const img = card.getAttribute('data-product-img');

    productTitle.textContent = name || 'Producto';
    productImg.src = img || '';
    productImg.alt = name || 'Producto';
    productPrice.textContent = price || '';
    productDesc.textContent = desc || '';

    productAddForm.action = `/cart/add/${id}`;

    productModal.classList.remove('is-hidden');
    document.body.classList.add('no-scroll');

    // opcional: centrar el modal de producto o reutilizar anclaje
    if (productPanel) {
      productPanel.style.top = '90px';
      productPanel.style.left = '50%';
      productPanel.style.transform = 'translateX(-50%)';
    }
  }

  function closeProductModal() {
    if (!productModal) return;
    productModal.classList.add('is-hidden');
    document.body.classList.remove('no-scroll');
  }

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-open-product]');
    if (!btn) return;
    const card = btn.closest('.product-card');
    if (!card) return;
    openProductFromCard(card);
  });

  productCloseX?.addEventListener('click', closeProductModal);
  productCloseFooter?.addEventListener('click', closeProductModal);

  productModal?.addEventListener('click', (e) => {
    const target = e.target;
    if (
      target &&
      target.getAttribute &&
      target.getAttribute('data-close') === 'true'
    ) {
      closeProductModal();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (
      e.key === 'Escape' &&
      productModal &&
      !productModal.classList.contains('is-hidden')
    ) {
      closeProductModal();
    }
  });
  // -----------------------
  // 4) AJAX: Añadir al carrito (sin recarga)
  // -----------------------
  const cartBadge = document.querySelector('.cart-badge');

  document.addEventListener('submit', async (e) => {
    const form = e.target;
    if (!form || form.getAttribute('data-ajax') !== 'add-to-cart') return;

    e.preventDefault();

    const productId = form.getAttribute('data-product-id');
    if (!productId) return;

    const formData = new FormData(form);

    try {
      const res = await fetch(`/api/cart/add/${productId}`, {
        method: 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'fetch' },
      });

      const data = await res.json();

      if (!res.ok || !data.ok) {
        alert(data.error || 'No se pudo añadir el producto.');
        return;
      }

      // 1) Badge
      if (cartBadge) cartBadge.textContent = String(data.total_units);

      // 2) Actualizar modal carrito
      const cartBody = document.getElementById('cart-modal-body');
      if (cartBody && typeof data.cart_html === 'string') {
        cartBody.innerHTML = data.cart_html;
      }
    } catch (err) {
      alert('Error de red. Inténtalo de nuevo.');
    }
  });
  // -----------------------
  // 5) AJAX: Chat (sin recarga)
  // -----------------------
  const chatForm = document.querySelector('.chat-widget-form');

  chatForm?.addEventListener('submit', async (e) => {
    const form = e.target;

    // Solo el form del chat widget
    if (!form || !form.classList.contains('chat-widget-form')) return;

    e.preventDefault();

    const input = form.querySelector('input[name="message"]');
    const msg = (input?.value || '').trim();
    if (!msg) return;

    // 1) Pintar mensaje del usuario inmediatamente (optimista)
    const messagesBox = document.getElementById('chat-messages');
    if (messagesBox) {
      const div = document.createElement('div');
      div.className = 'message user';
      div.innerHTML = `<strong>Usuario:</strong><p></p>`;
      div.querySelector('p').textContent = msg;
      messagesBox.appendChild(div);
      messagesBox.scrollTop = messagesBox.scrollHeight;
    }

    // limpiar input
    input.value = '';

    // 2) Llamar API
    const fd = new FormData();
    fd.append('message', msg);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        body: fd,
        headers: { 'X-Requested-With': 'fetch' },
      });

      const data = await res.json();

      if (!res.ok || !data.ok) {
        alert(data.error || 'Error procesando el mensaje.');
        return;
      }

      // 3) Append del último mensaje del bot (viene con HTML seguro)
      if (messagesBox && data.last_messages) {
        // esperamos el último sea bot
        const last = data.last_messages[data.last_messages.length - 1];
        if (last && last[0] === 'bot') {
          const div = document.createElement('div');
          div.className = 'message assistant';
          div.innerHTML = `<strong>Asistente:</strong><div class="assistant-message-content"></div>`;
          div.querySelector('.assistant-message-content').innerHTML = last[1]; // HTML del bot
          messagesBox.appendChild(div);
          messagesBox.scrollTop = messagesBox.scrollHeight;
        }
      }

      // 4) Badge
      const cartBadge = document.querySelector('.cart-badge');
      if (cartBadge) cartBadge.textContent = String(data.total_units ?? 0);

      // 5) Actualizar contenido del carrito modal
      const cartBody = document.getElementById('cart-modal-body');
      if (cartBody && typeof data.cart_html === 'string') {
        cartBody.innerHTML = data.cart_html;
      }
    } catch (err) {
      alert('Error de red. Inténtalo de nuevo.');
    }
  });
})();

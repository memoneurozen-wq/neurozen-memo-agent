export function displayMessage(container, text, sender) {
  const message = document.createElement("div");
  
  // Remove espaços invisíveis e trim corretamente
  const cleanText = text.replace(/^\s+|\s+$/g, '').replace(/[\u200B-\u200D\uFEFF]/g, '');
  message.textContent = cleanText;
  
  message.className = `chat-bubble ${sender}`;
  
  // Remove estilos inline conflitantes - deixa só o CSS fazer o trabalho
  message.style.cssText = '';
  
  container.appendChild(message);
  container.scrollTop = container.scrollHeight;
}

// Exibe múltiplos balões com pausa entre eles
export async function displayMessageSequence(container, messages, sender) {
  for (const msg of messages) {
    await new Promise((resolve) => setTimeout(resolve, 1500));
    displayMessage(container, msg, sender);
  }
}

export function showTyping(container) {
  // Remove typing anterior se existir
  removeTyping(container);
  
  const typingIndicator = document.createElement("div");
  typingIndicator.textContent = "Digitando...";
  typingIndicator.id = "typing";
  
  container.appendChild(typingIndicator);
  container.scrollTop = container.scrollHeight;
}

export function removeTyping(container) {
  const typing = document.getElementById("typing");
  if (typing && typing.parentNode === container) {
    container.removeChild(typing);
  }
}
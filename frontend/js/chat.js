import { agentPrompt } from "./agent.js";
import { displayMessage, showTyping, removeTyping } from "./ui.js";

// URL do servidor no Render — substitua pela sua URL real após o deploy
const API_URL = "https://neurozen-memo-agent.onrender.com";

// Espera o DOM carregar
window.addEventListener("DOMContentLoaded", () => {
  const chatMessages = document.getElementById("chat-messages");
  const sendBtn = document.getElementById("send-btn");
  const userInput = document.getElementById("user-input");

  // Variáveis de controle
  let isMemoTyping = false;
  let shouldPauseMemo = false;

  // Frases de boas-vindas variadas
  const welcomeSequences = [
    [
      "Oi! 👋 Eu sou o Memo, tudo bem?",
      "Faço parte da equipe do NeuroZen e conheço bem o livro.",
      "Se tiver dúvidas ou quiser saber se ele é pra você, estou por aqui!"
    ],
    [
      "Olá! 😊 Seja bem-vindo ao NeuroZen.",
      "Meu nome é Memo, li o livro do começo ao fim.",
      "Posso te ajudar a entender se ele é o que você está procurando."
    ],
    [
      "E aí! 👋 Tudo certo?",
      "Sou o Memo da equipe do NeuroZen. Já mergulhei no conteúdo do livro.",
      "Quer trocar uma ideia e ver se ele faz sentido pra você?"
    ]
  ];

  function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Detecta quando usuário está digitando
  userInput.addEventListener("input", () => {
    if (isMemoTyping) {
      shouldPauseMemo = true;
    }
  });

  // Exibe sequência de mensagens com simulação de digitação
  async function showWelcomeMessage() {
    const sequence = welcomeSequences[Math.floor(Math.random() * welcomeSequences.length)];

    for (let i = 0; i < sequence.length; i++) {
      const msg = sequence[i];
      const typingTime = 30 * msg.length + 500;

      if (i !== 0) {
        await delay(600 + Math.random() * 700);
      }

      showTyping(chatMessages);
      await delay(typingTime);
      removeTyping(chatMessages);

      displayMessage(chatMessages, msg, "bot");
    }
  }

  // Quebra resposta em múltiplas mensagens
  function splitResponse(response) {
    const sentences = response
      .split(/(?<=[.!?])\s+|\n+/)
      .filter(sentence => sentence.trim().length > 0);

    const messages = [];
    let currentMessage = "";

    for (const sentence of sentences) {
      if (currentMessage.length + sentence.length > 120 && currentMessage.length > 0) {
        messages.push(currentMessage.trim());
        currentMessage = sentence;
      } else {
        currentMessage += (currentMessage ? " " : "") + sentence;
      }
    }

    if (currentMessage.trim()) {
      messages.push(currentMessage.trim());
    }

    return messages.length > 0 ? messages : [response];
  }

  // Envia múltiplas mensagens com pausas
  async function sendMultipleMessages(messages) {
    isMemoTyping = true;
    shouldPauseMemo = false;

    for (let i = 0; i < messages.length; i++) {
      if (shouldPauseMemo) {
        removeTyping(chatMessages);
        displayMessage(chatMessages, "Pode falar! Estou ouvindo... 😊", "bot");
        isMemoTyping = false;
        return;
      }

      const message = messages[i];
      const typingTime = Math.max(message.length * 40, 800);

      if (i > 0) {
        await delay(800 + Math.random() * 600);

        if (shouldPauseMemo) {
          removeTyping(chatMessages);
          displayMessage(chatMessages, "Pode falar! Estou ouvindo... 😊", "bot");
          isMemoTyping = false;
          return;
        }
      }

      showTyping(chatMessages);
      await delay(typingTime);

      if (shouldPauseMemo) {
        removeTyping(chatMessages);
        displayMessage(chatMessages, "Pode falar! Estou ouvindo... 😊", "bot");
        isMemoTyping = false;
        return;
      }

      removeTyping(chatMessages);
      displayMessage(chatMessages, message, "bot");
    }

    isMemoTyping = false;
  }

  // Inicia mensagem de boas-vindas após um delay
  setTimeout(() => {
    showWelcomeMessage();
  }, 1000);

  // Eventos
  sendBtn.addEventListener("click", handleUserMessage);
  userInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      handleUserMessage();
    }
  });

  // Envio da mensagem do usuário e resposta da API
  async function handleUserMessage() {
    const userMessage = userInput.value.trim();
    if (!userMessage) return;

    shouldPauseMemo = true;
    removeTyping(chatMessages);

    displayMessage(chatMessages, userMessage, "user");
    userInput.value = "";

    isMemoTyping = false;
    shouldPauseMemo = false;

    showTyping(chatMessages);

    try {
      // Gera ou recupera o session_id persistido no navegador
      // Garante que o Memo reconhece o usuário mesmo após fechar e reabrir a aba
      let sessionId = localStorage.getItem("neurozen_session_id");
      if (!sessionId) {
        sessionId = "user_" + Math.random().toString(36).substr(2, 9);
        localStorage.setItem("neurozen_session_id", sessionId);
      }

      // Chama o servidor hospedado no Render
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: userMessage,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const botResponse = data.response;

      // log para debug: mostra quantas memórias foram usadas nesta resposta
      console.log(`Memórias utilizadas: ${data.memories_retrieved}`);

      removeTyping(chatMessages);

      const messages = splitResponse(botResponse);
      await sendMultipleMessages(messages);

    } catch (error) {
      console.error("Erro na API:", error);
      removeTyping(chatMessages);

      const fallbackResponses = [
        "Desculpe, estou com uma instabilidade temporária. Que tal tentar novamente em alguns segundos?",
        "Ops! Parece que tive um probleminha técnico. Pode repetir sua pergunta?",
        "Nossa, algo deu errado por aqui. Mas fique à vontade para me perguntar sobre o NeuroZen!"
      ];

      const randomFallback = fallbackResponses[Math.floor(Math.random() * fallbackResponses.length)];
      displayMessage(chatMessages, randomFallback, "bot");
    }
  }
});
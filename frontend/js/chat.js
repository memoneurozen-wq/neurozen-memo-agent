import { agentPrompt } from "./agent.js";
import { displayMessage, showTyping, removeTyping } from "./ui.js";

// Espera o DOM carregar
window.addEventListener("DOMContentLoaded", () => {
  const chatMessages = document.getElementById("chat-messages");
  const sendBtn = document.getElementById("send-btn");
  const userInput = document.getElementById("user-input");

  // Variáveis de controle
  let isRafaTyping = false;
  let shouldPauseRafa = false;

  // Frases de boas-vindas variadas (corrigidas)
  const welcomeSequences = [
    [
      "Oi! 👋 Eu sou o Rafa, tudo bem?",
      "Faço parte da equipe do NeuroZen e conheço bem o livro.",
      "Se tiver dúvidas ou quiser saber se ele é pra você, estou por aqui!"
    ],
    [
      "Olá! 😊 Seja bem-vindo ao NeuroZen.",
      "Meu nome é Rafa, li o livro do começo ao fim.",
      "Posso te ajudar a entender se ele é o que você está procurando."
    ],
    [
      "E aí! 👋 Tudo certo?",
      "Sou o Rafa da equipe do NeuroZen. Já mergulhei no conteúdo do livro.",
      "Quer trocar uma ideia e ver se ele faz sentido pra você?"
    ]
  ];

  function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Detecta quando usuário está digitando
  userInput.addEventListener("input", () => {
    if (isRafaTyping) {
      shouldPauseRafa = true;
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
    // Quebra por pontos finais, quebras de linha, ou frases longas
    const sentences = response
      .split(/(?<=[.!?])\s+|\n+/)
      .filter(sentence => sentence.trim().length > 0);
    
    const messages = [];
    let currentMessage = "";
    
    for (const sentence of sentences) {
      // Se a mensagem atual + nova frase fica muito longa (mais de 120 chars)
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
    isRafaTyping = true;
    shouldPauseRafa = false;

    for (let i = 0; i < messages.length; i++) {
      // Verifica se usuário começou a digitar
      if (shouldPauseRafa) {
        removeTyping(chatMessages);
        displayMessage(chatMessages, "Pode falar! Estou ouvindo... 😊", "bot");
        isRafaTyping = false;
        return;
      }

      const message = messages[i];
      const typingTime = Math.max(message.length * 40, 800); // Mínimo 800ms

      // Pausa entre mensagens (exceto a primeira)
      if (i > 0) {
        await delay(800 + Math.random() * 600);
        
        // Verifica novamente se usuário está digitando
        if (shouldPauseRafa) {
          removeTyping(chatMessages);
          displayMessage(chatMessages, "Pode falar! Estou ouvindo... 😊", "bot");
          isRafaTyping = false;
          return;
        }
      }

      showTyping(chatMessages);
      await delay(typingTime);
      
      // Última verificação antes de enviar
      if (shouldPauseRafa) {
        removeTyping(chatMessages);
        displayMessage(chatMessages, "Pode falar! Estou ouvindo... 😊", "bot");
        isRafaTyping = false;
        return;
      }

      removeTyping(chatMessages);
      displayMessage(chatMessages, message, "bot");
    }

    isRafaTyping = false;
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

    // Para qualquer resposta do Rafa em andamento
    shouldPauseRafa = true;
    removeTyping(chatMessages);

    displayMessage(chatMessages, userMessage, "user");
    userInput.value = "";

    // Reset das variáveis de controle
    isRafaTyping = false;
    shouldPauseRafa = false;

    showTyping(chatMessages);

    try {
      // Configuração para a API da Groq
      const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer SUA CHAVE_DE_API_GROQ",
        },
        body: JSON.stringify({
          messages: [
            { role: "system", content: agentPrompt },
            { role: "user", content: userMessage },
          ],
          model: "llama3-70b-8192",
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const botResponse = data.choices[0].message.content;

      removeTyping(chatMessages);

      // Quebra a resposta em múltiplas mensagens
      const messages = splitResponse(botResponse);
      
      // Envia mensagens com pausas
      await sendMultipleMessages(messages);

    } catch (error) {
      console.error("Erro na API:", error);
      removeTyping(chatMessages);
      
      // Resposta de fallback mais natural
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
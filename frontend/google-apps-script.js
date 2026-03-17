function doGet(e) {
  Logger.log("🚀 Iniciando doGet - NeuroZen...");

  if (!e || !e.parameter || !e.parameter.email) {
    Logger.log("❌ ERRO: Nenhum dado GET recebido!");
    return ContentService.createTextOutput(JSON.stringify({
      "status": "error",
      "message": "Email obrigatório"
    })).setMimeType(ContentService.MimeType.JSON);
  }

  try {
    var email = e.parameter.email.trim();
    Logger.log("✅ Email recebido: " + email);

    // ID da sua planilha NeuroZen
    var sheetId = "1E8...VI9c"; //ID da sua planilha do google sheets
    var spreadsheet = SpreadsheetApp.openById(sheetId);
    var sheet = spreadsheet.getActiveSheet();
    
    Logger.log("✅ Planilha encontrada: " + sheet.getName());

    // Adiciona na planilha
    sheet.appendRow([new Date(), email]);
    Logger.log("✅ Email salvo na planilha NeuroZen.");

    // 📧 1. ENVIA EMAIL DE AGRADECIMENTO PARA QUEM SE CADASTROU
    try {
      Logger.log("🔄 Enviando email de agradecimento para: " + email);
      
      MailApp.sendEmail({
        to: email, // ← PARA QUEM SE CADASTROU
        subject: "NeuroZen - Obrigado pelo seu interesse! 🧠✨",
        htmlBody: `
          <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">Obrigado pelo seu interesse no NeuroZen! 🧠✨</h2>
            
            <p>Olá,</p>
            
            <p>Muito obrigado por demonstrar interesse no livro <strong>"NeuroZen - Guia da Mente Criativa com IA"</strong>!</p>
            
            <p>Você será um dos primeiros a saber sobre:</p>
            <ul style="color: #374151;">
              <li>🚀 <strong>Lançamento oficial</strong></li>
              <li>💰 <strong>Ofertas exclusivas</strong></li>
              <li>🎁 <strong>Bônus especiais para os primeiros leitores</strong></li>
              <li>📚 <strong>Conteúdos exclusivos sobre IA e criatividade</strong></li>
            </ul>
            
            <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
              <p style="margin: 0;"><strong>💡 Dica:</strong> Adicione nosso email à sua lista de contatos para não perder nenhuma novidade!</p>
            </div>
            
            <p>Fique atento ao seu email!</p>
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
            
            <p>Abraços,<br>
            <strong>Equipe do Seu Produto</strong><br>
            <a href="mailto:seu_email@gmail.com" style="color: #2563eb;">seu_email@gmail.com</a></p>
          </div>
        `
      });
      
      Logger.log("✅ Email de agradecimento ENVIADO para: " + email);
      
    } catch (emailError) {
      Logger.log("❌ ERRO ao enviar email de agradecimento: " + emailError.message);
    }

    // 📧 2. ENVIA NOTIFICAÇÃO DE NOVO LEAD PARA A EQUIPE
    try {
      Logger.log("🔄 Enviando notificação de lead para: neurozenbook@gmail.com");
      
      MailApp.sendEmail({
        to: "neurozenbook@gmail.com", // ← PARA A EQUIPE
        subject: "🎯 Novo Lead NeuroZen!",
        htmlBody: `
          <h3>📢 Novo interessado no NeuroZen!</h3>
          <p><strong>Email:</strong> ${email}</p>
          <p><strong>Data:</strong> ${new Date()}</p>
          <p><strong>Origem:</strong> Landing Page NeuroZen</p>
          <br>
          <p>Já pode incluir no funil de vendas! 🚀</p>
        `
      });
      
      Logger.log("✅ Notificação de lead ENVIADA para: neurozenbook@gmail.com");
      
    } catch (adminEmailError) {
      Logger.log("❌ ERRO ao enviar notificação de lead: " + adminEmailError.message);
    }

    return ContentService.createTextOutput(JSON.stringify({
      "status": "success",
      "message": "Email cadastrado com sucesso"
    })).setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    Logger.log("❌ ERRO GERAL: " + error.message);
    return ContentService.createTextOutput(JSON.stringify({
      "status": "error",
      "message": error.message
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

function doPost(e) {
  return doGet(e);
}
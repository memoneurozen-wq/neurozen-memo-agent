document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("email-form");
  const scriptURL = URL_DO_SCRIPT;

  form.addEventListener("submit", function (e) {
    e.preventDefault();

    const emailInput = form.querySelector("input[type='email']");
    const email = emailInput.value.trim();

    if (!email) {
      alert("Digite um e-mail válido!");
      return;
    }

    fetch(`${scriptURL}?email=${encodeURIComponent(email)}`)
      .then((response) => response.json())
      .then((data) => {
        if (data.status === "success") {
          alert("✅ Obrigado! Seu e-mail foi cadastrado com sucesso.");
          emailInput.value = "";
          window.location.href = "thanks.html";
        } else {
          alert("❌ Houve um erro ao cadastrar. Tente novamente.");
        }
      })
      .catch((error) => {
        console.error("Erro:", error);
        alert("❌ Houve um erro inesperado. Tente novamente.");
      });
  });
});
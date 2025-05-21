const textarea_feedback = document.querySelector("#texto_feedback")
const contador = document.querySelector("#contador")
const tamanho_maximo = 300

textarea_feedback.addEventListener("input", () => {
    restante = tamanho_maximo - textarea_feedback.value.length
    contador.innerHTML = restante
})
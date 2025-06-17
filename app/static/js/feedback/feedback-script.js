const textarea_feedback = document.querySelector("#texto_feedback")
const contador_feedback = document.querySelector("#contador")
const tamanho_maximo = 300

textarea_feedback.addEventListener("input", () => {
    restante = tamanho_maximo - textarea_feedback.value.length
    contador_feedback.innerHTML = restante
})

if (localStorage.getItem('modo-escuro') === 'true') {
    document.body.classList.add('modo-escuro')
}
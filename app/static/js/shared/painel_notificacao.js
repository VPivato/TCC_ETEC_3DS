// PAINEL NOTIFICAÇÕES
const painel = document.getElementById('painel-notif')
const sino = document.getElementById('sino')
const lista = document.getElementById('lista-notif')
const contador = document.getElementById('notif-contador')
const fechar_notif = document.querySelector("#fechar-notif")
sino.addEventListener('click', () => {
    painel.classList.toggle('hidden')
    contador.style.display = 'none'
    fetch('/notificacao/marcar_como_vista', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
})
fechar_notif.addEventListener("click", () => {
    painel.classList.add("hidden")
})
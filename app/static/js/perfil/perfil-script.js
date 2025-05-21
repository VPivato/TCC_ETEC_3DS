const botoes = document.querySelectorAll('.aside-wrapper')
const conteudos = document.querySelectorAll('.conteudo-pagina')

// MUDANÇA DE PÁGINA MENU LATERAL
botoes.forEach(botao => {
    botao.addEventListener("click", () => {
        // Remover classe 'ativo' de todos os botões
        botoes.forEach(b => b.classList.remove('active'))

        // Adicionar 'ativo' ao botão clicado
        botao.classList.add('active')

        // Esconder todos os conteúdos
        conteudos.forEach(c => c.classList.remove('ativo'))

        // Mostrar conteúdo correspondente
        const id = botao.id.replace('-wrapper', '')
        const conteudoSelecionado = document.getElementById(`conteudo-${id}`)
        if (conteudoSelecionado) {
            conteudoSelecionado.classList.add('ativo')
            // Scroll para o conteúdo em telas pequenas
            if (window.innerWidth <= 1024) {
                conteudoSelecionado.scrollIntoView({ behavior: "smooth" })
            }
        }
    })
})

// MODO ESCURO
const modo_escuro_toggle = document.getElementById('modo-escuro-toggle')
modo_escuro_toggle.addEventListener('change', () => {
    document.body.classList.toggle('modo-escuro')
    localStorage.setItem('modo-escuro', document.body.classList.contains('modo-escuro'))
})
// Restaurar ao carregar a página
if (localStorage.getItem('modo-escuro') === 'true') {
    document.body.classList.add('modo-escuro')
    modo_escuro_toggle.checked = true
}

// PAINEL NOTIFICAÇÕES
const painel = document.getElementById('painel-notif')
const sino = document.getElementById('sino')
const lista = document.getElementById('lista-notif')
const contador = document.getElementById('notif-contador')
let notifNaoLidas = 0
sino.addEventListener('click', () => {
    painel.classList.toggle('hidden')
    notifNaoLidas = 0
    contador.style.display = 'none'
})

// CONFIRMAÇÃO SAIR 
document.querySelector('#sair-wrapper').addEventListener("click", () => {
    if (confirm("Deseja mesmo sair?")) {
        window.location.href = "sair"
    }
    else {
        window.location.href = "perfil"
    }
});
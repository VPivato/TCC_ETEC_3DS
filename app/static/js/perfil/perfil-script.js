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
const fechar_notif = document.querySelector("#fechar-notif")
sino.addEventListener('click', () => {
    painel.classList.toggle('hidden')
    contador.style.display = 'none'
})
fechar_notif.addEventListener("click", () => {
    painel.classList.add("hidden")
})

// DESATIVAR NOTIFCAÇÕES
const desativar_notificacoes_toggle = document.querySelector("#notif-toggle")
const notif_container = document.querySelector("#notif-container")
desativar_notificacoes_toggle.addEventListener("change", () => {
    localStorage.setItem('desativar-notificacoes', desativar_notificacoes_toggle.checked)
    if (desativar_notificacoes_toggle.checked) {
        notif_container.classList.add("hidden")
    }
    else {
        notif_container.classList.remove("hidden")
    }
})
// Restaurar ao carregar a página
if (localStorage.getItem('desativar-notificacoes') === 'true') {
    desativar_notificacoes_toggle.checked = true
    notif_container.classList.add("hidden")
}

// RECEBER NOTIFICAÇÕES EM TEMPO REAL
const socket = io();
socket.on("nova_notificacao", function (data) {
    const ul = document.querySelector("#lista-notif");
    const li = document.createElement("li");
    ul.textContent = ""
    li.className = "notificacao";
    li.textContent = data.mensagem;
    ul.prepend(li);
});

// CONFIRMAÇÃO SAIR 
document.querySelector('#sair-wrapper').addEventListener("click", () => {
    if (confirm("Deseja mesmo sair?")) {
        window.location.href = "sair"
    }
    else {
        window.location.href = "perfil"
    }
});
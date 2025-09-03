const botoes = document.querySelectorAll('.aside-wrapper')
const conteudo_conf = document.querySelector("#conteudo-conf")
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

document.getElementById('edit-pfp').addEventListener('click', function (e) {
    e.preventDefault();
    document.getElementById('foto-input').click();
});
document.getElementById('foto-perfil').addEventListener('click', () => {
    document.getElementById('foto-input').click();
});
// Preview da imagem selecionada
document.getElementById('foto-input').addEventListener('change', function (e) {
    const file = e.target.files[0];
    const img = document.getElementById('foto-perfil');

    if (file) {
        const reader = new FileReader();

        reader.onload = function (event) {
            img.src = event.target.result;
        }

        reader.readAsDataURL(file);
    }
});

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

// DESATIVAR NOTIFICAÇÕES
const desativar_notificacoes_toggle = document.querySelector("#notif-toggle")
const notif_container = document.querySelector("#notif-container")
desativar_notificacoes_toggle.addEventListener("change", () => {
    fetch('/notificacao/atualizar_notificacoes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ notificacoes_ativas: !desativar_notificacoes_toggle.checked })
    })
    localStorage.setItem('desativar-notificacoes', desativar_notificacoes_toggle.checked)
    if (desativar_notificacoes_toggle.checked) {
        painel.innerHTML = ""
        const div = document.createElement("div")
        const span = document.createElement("span")
        span.id = "fechar-notif"
        span.textContent = "x"
        div.classList.add("notificacao")
        div.textContent = "Ative as notificações em configurações."
        painel.appendChild(span)
        painel.appendChild(div)
        span.addEventListener("click", () => {
            painel.classList.add("hidden")
        })
    }
    else {
        alert("Recarrege a página para fazer efeito.")
    }
})
// Restaurar ao carregar a página
if (localStorage.getItem('desativar-notificacoes') === 'true') {
    fetch('/notificacao/atualizar_notificacoes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ notificacoes_ativas: localStorage.getItem('desativar-notificacoes') })
    })
    desativar_notificacoes_toggle.checked = true
    painel.innerHTML = ""
    const div = document.createElement("div")
    const span = document.createElement("span")
    span.id = "fechar-notif"
    span.textContent = "x"
    div.classList.add("notificacao")
    div.textContent = "Ative as notificações em configurações."
    painel.appendChild(span)
    painel.appendChild(div)
    span.addEventListener("click", () => {
        painel.classList.add("hidden")
    })
}

// CONFIRMAÇÃO SAIR 
document.querySelector('#sair-wrapper').addEventListener("click", () => {
    Swal.fire({
        title: 'Deseja mesmo sair?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Sair',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = "/perfil/sair"
        }
        else {
            window.location.href = ""
        }
    });
});

//CONFIRMAÇÃO EXCLUIR CONTA
document.getElementById('form-excluir-conta').addEventListener('submit', function (e) {
    e.preventDefault()
    Swal.fire({
        title: 'Excluir sua conta?',
        icon: 'warning',
        text: 'Essa ação é IRREVERSÍVEL',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        confirmButtonText: 'Sim, excluir',
        cancelButtonText: 'Não, voltar'
    }).then((result) => {
        if (result.isConfirmed) {
            e.target.submit()
        }
        else {
            window.location.href = ""
        }
    })
})


const ctxCategoria = document.getElementById('grafico-categoria').getContext('2d');
let graficoCategoria = new Chart(ctxCategoria, {
    type: 'pie',
    data: {
        labels: [], // categorias
        datasets: [{
            label: 'Gasto por categoria',
            data: [], // valores por categoria
            backgroundColor: ['#0d6efd', '#198754', '#ffc107', '#dc3545', '#6f42c1'],
            hoverOffset: 15
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                position: 'bottom',
            },
            tooltip: {
                callbacks: {
                    label: function (context) {
                        const valor = context.raw;
                        return `R$ ${valor.toFixed(2)}`;
                    }
                }
            },
            datalabels: {
                color: '#fff',
                formatter: (value, context) => {
                    const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                    const perc = (value / total * 100).toFixed(1);
                    return `${perc}%`;
                },
                font: {
                    weight: 'bold',
                    size: 14
                }
            }
        }
    },
    plugins: [ChartDataLabels]  // ativa o plugin
});


// Função para atualizar estatísticas (AJAX)
function atualizarEstatisticas() {
    const periodo = document.getElementById('filtro-periodo').value;
    fetch('/perfil/estatisticas-usuario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: '{{ session["user_id"] }}', periodo })
    })
        .then(res => res.json())
        .then(data => {
            document.getElementById('total-pedidos').textContent = data.total_pedidos;
            document.getElementById('total-gasto').textContent = `R$ ${data.total_gasto.toFixed(2)}`;
            document.getElementById('media-pedido').textContent = `R$ ${data.media_pedido.toFixed(2)}`;

            const topProdutos = document.getElementById('top-produtos');
            topProdutos.innerHTML = '';
            data.top_produtos.forEach(prod => {
                const li = document.createElement('li');
                li.className = 'list-group-item d-flex justify-content-between align-items-center';
                li.innerHTML = `${prod.nome} <span class="badge bg-primary rounded-pill">${prod.quantidade} unidades</span>`;
                topProdutos.appendChild(li);
            });

            graficoCategoria.data.labels = data.gasto_por_categoria.labels;
            graficoCategoria.data.datasets[0].data = data.gasto_por_categoria.valores;
            graficoCategoria.update();
        });
}

document.addEventListener('DOMContentLoaded', atualizarEstatisticas);
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".form-cancelar-pedido").forEach(form => {
        form.addEventListener("submit", function (e) {
            e.preventDefault(); // impede envio imediato

            Swal.fire({
                title: "Cancelar pedido?",
                text: "Esta ação não poderá ser desfeita.",
                icon: "warning",
                showCancelButton: true,
                confirmButtonColor: "#d33",
                cancelButtonColor: "#6c757d",
                confirmButtonText: "Sim, cancelar",
                cancelButtonText: "Não",
                heightAuto: false
            }).then((result) => {
                if (result.isConfirmed) {
                    form.submit(); // envia o formulário se confirmado
                }
            });
        });
    });
});
document.addEventListener('DOMContentLoaded', () => {
    // nome das seções possíveis: 'geral', 'comprovantes', 'stats', 'conf'
    const DEFAULT_TAB = 'geral';
    const asideButtons = document.querySelectorAll('.aside-wrapper');
    const contents = document.querySelectorAll('.conteudo-pagina');

    function activateTab(tabName) {
        if (!tabName) tabName = DEFAULT_TAB;

        // remover classes
        asideButtons.forEach(b => b.classList.remove('active'));
        contents.forEach(c => c.classList.remove('ativo'));

        // ativar botão e conteúdo correspondentes apenas se existir conteúdo
        const content = document.getElementById(`conteudo-${tabName}`);
        if (!content) return;  // sai se não houver conteúdo

        const btn = document.getElementById(`${tabName}-wrapper`);
        if (btn) btn.classList.add('active');
        content.classList.add('ativo');

        // salva no sessionStorage
        try { sessionStorage.setItem('perfil_tab', tabName); } catch (e) { }
    }

    // determina aba inicial: primeiro hash, depois sessionStorage, depois default
    let initialTab = null;
    if (location.hash && location.hash.length > 1) {
        initialTab = location.hash.slice(1); // remove '#'
    } else {
        try { initialTab = sessionStorage.getItem('perfil_tab') || null; } catch (e) { initialTab = null; }
    }
    initialTab = initialTab || DEFAULT_TAB;
    activateTab(initialTab);

    // atualiza URL (sem scroll) e storage quando usuário clica no menu lateral
    asideButtons.forEach(botao => {
        botao.addEventListener('click', (e) => {
            const tab = botao.id.replace('-wrapper', '');
            // altera a URL sem provocar scroll
            history.replaceState(null, '', `#${tab}`);
            activateTab(tab);
        });
    });

    // garantir que, se alguém mudar manualmente o hash (ex: link externo), a aba atualize
    window.addEventListener('hashchange', () => {
        const tab = location.hash.slice(1) || sessionStorage.getItem('perfil_tab') || DEFAULT_TAB;
        activateTab(tab);
    });

    // Ao clicar em links de paginação, adiciona o hash atual ao href para preservar aba
    // (previne comportamento padrão apenas para injetar o hash)
    document.querySelectorAll('.pagination a').forEach(link => {
        link.addEventListener('click', (ev) => {
            ev.preventDefault();
            const href = link.getAttribute('href');
            const currentTab = (location.hash && location.hash.length > 1) ? location.hash.slice(1) : (sessionStorage.getItem('perfil_tab') || DEFAULT_TAB);
            // navega com o hash anexado
            window.location.href = href + `#${currentTab}`;
        });
    });
});

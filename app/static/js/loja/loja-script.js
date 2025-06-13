new Swiper('.card-wrapper', {
    loop: false,
    spaceBetween: 20,

    navigation: {
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev',
    },

    breakpoints: {
        0: {
            slidesPerView: 1.3
        },
        576: {
            slidesPerView: 2
        },
        768: {
            slidesPerView: 2.5
        },
        992: {
            slidesPerView: 3
        },
        1280: {
            slidesPerView: 4
        }
    },
});

function feedbackVisualBotao(idProduto) {
    const botao = document.getElementById(`btn-produto-${idProduto}`);
    if (!botao) return;

    botao.classList.add('btn-adicionado');
    setTimeout(() => {
        botao.classList.remove('btn-adicionado');
    }, 600);
}

let carrinho = {};
let total = 0;
function adicionarProduto(id, nome, preco, estoqueDisponivel) {
    if (carrinho[id]) {
        if (carrinho[id].quantidade >= estoqueDisponivel) {
            alert(`Estoque insuficiente! Apenas ${estoqueDisponivel} unidades disponíveis.`);
            return;
        }
        carrinho[id].quantidade += 1;
    } else {
        carrinho[id] = {
            nome: nome,
            preco: parseFloat(preco),
            quantidade: 1,
            estoque: estoqueDisponivel
        };
    }
    atualizarCarrinho();
    feedbackVisualBotao(id);
}

function atualizarCarrinho() {
    const lista = document.getElementById('carrinho');
    const listaMobile = document.getElementById('carrinho-mobile');
    lista.innerHTML = '';
    listaMobile.innerHTML = '';
    total = 0;

    for (const id in carrinho) {
        const item = carrinho[id];
        const subtotal = item.preco * item.quantidade;
        total += subtotal;

        const cardHTML = `
            <div class="card shadow-sm mb-1">
                <div class="card-body d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="card-title mb-1">${item.nome}</h6>
                        <p class="card-subtitle text-muted small mb-0">R$ ${item.preco.toFixed(2)} cada</p>
                        <p class="mb-0">Quantidade: ${item.quantidade}</p>
                    </div>
                    <div class="text-end">
                        <button class="btn btn-sm btn-outline-danger mb-2" onclick="removerProduto(${id})">
                            <i class="bi bi-dash-circle"></i> Remover
                        </button>
                        <div class="fw-bold">R$ ${subtotal.toFixed(2)}</div>
                    </div>
                </div>
            </div>
        `;

        lista.insertAdjacentHTML('beforeend', cardHTML);
        listaMobile.insertAdjacentHTML('beforeend', cardHTML);
    }

    document.getElementById('total').textContent = total.toFixed(2);
    document.getElementById('total-mobile').textContent = total.toFixed(2);
}

function removerProduto(id) {
    if (carrinho[id]) {
        carrinho[id].quantidade -= 1;
        if (carrinho[id].quantidade <= 0) {
            delete carrinho[id];
        }
        atualizarCarrinho();
    }
}

async function finalizarCompra() {
    if (Object.keys(carrinho).length === 0) {
        Swal.fire({
            icon: 'warning',
            title: 'Carrinho vazio!',
            text: 'Adicione produtos antes de finalizar a compra.'
        });
        return;
    }

    try {
        const resposta = await fetch('/loja/finalizar-compra', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ carrinho })
        });

        const resultado = await resposta.json();

        if (resposta.ok) {
            Swal.fire({
                icon: 'success',
                title: 'Compra finalizada!',
                confirmButtonText: 'OK',
            }).then(() => {
                location.reload();
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Erro ao finalizar',
                text: resultado.erro || 'Ocorreu um erro inesperado.'
            });
        }
    } catch (erro) {
        console.error('Erro na requisição:', erro);
        Swal.fire({
            icon: 'error',
            title: 'Erro de rede',
            text: 'Não foi possível se conectar ao servidor.'
        });
    }
}

function cancelarCompra() {
    if (confirm('Tem certeza que deseja cancelar a compra?')) {
        carrinho = {};
        atualizarCarrinho();
    }
}

const marquees = document.querySelectorAll('.marquee-container');
marquees.forEach(container => {
    const texto = container.querySelector('.marquee-text');

    // Compara a largura do texto com o container
    if (texto.scrollWidth > container.clientWidth) {
        // Adiciona classe no container pai (ex: <h2>)
        container.parentElement.classList.add('marquee-animar');
    }
});

if (localStorage.getItem('modo-escuro') === 'true') {
    document.body.classList.add('modo-escuro')
}
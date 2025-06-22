const swiper = new Swiper('.mySwiper', {
    slidesPerView: 1,
    spaceBetween: 30,
    loop: true,

    navigation: {
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev'
    },

    observer: true,
    observeParents: true,
});

// CONFIRMAÇÃO SAIR 
document.querySelector('#sair-btn').addEventListener("click", () => {
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

document.addEventListener('DOMContentLoaded', () => {
    // GRÁFICO PRODUTOS
    const container_produtos = document.getElementById('grafico-produtos-container');
    const labels_produtos = JSON.parse(container_produtos.dataset.labels_produtos);
    const values_produtos = JSON.parse(container_produtos.dataset.values_produtos);
    const ctxProdutos = document.getElementById('grafico-produtos').getContext('2d');
    new Chart(ctxProdutos, {
        type: 'bar',
        data: {
            labels: labels_produtos,
            datasets: [{
                label: 'Qtd. em Estoque',
                data: values_produtos,
                backgroundColor: '#0d6efd'
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: context => ` ${context.parsed.x} unidades`
                    }
                },
                title: {
                    display: true,
                    text: 'Produtos com Menor Estoque',
                    font: {
                        size: 18,
                        weight: 'bold'
                    },
                    padding: {
                        top: 10,
                        bottom: 20
                    }
                },
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 2
                    },
                    grid: {
                        color: 'rgba(0,0,0,0.05)'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(0,0,0,0.05)'
                    }
                }
            }
        }
    });


    // GRÁFICO PEDIDOS
    const container_pedidos = document.getElementById('grafico-pedidos-container');
    const labels_pedidos = JSON.parse(container_pedidos.dataset.labels_pedidos);
    const values_pedidos = JSON.parse(container_pedidos.dataset.values_pedidos);
    const ctx = document.getElementById('grafico-pedidos').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels_pedidos,
            datasets: [{
                label: 'Pedidos',
                data: values_pedidos,
                fill: true,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.2)',
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                title: {
                    display: true,
                    text: 'Vendas nas Últimas Semanas',
                    font: { size: 18, weight: 'bold' },
                    padding: { top: 10, bottom: 20 }
                },
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            pointBackgroundColor: '#0d6efd',
            pointRadius: 4,
        }
    });


    // GRÁFICO DE CRESCIMENTO DE USUÁRIOS - BANCO DE DADOS
    const container_usuarios = document.getElementById('grafico-usuarios-container');
    const labels_usuarios = JSON.parse(container_usuarios.dataset.labels_usuarios);
    const values_usuarios = JSON.parse(container_usuarios.dataset.values_usuarios);
    const ctxUsuarios = document.getElementById('grafico-usuarios').getContext('2d');
    new Chart(ctxUsuarios, {
        type: 'line',
        data: {
            labels: labels_usuarios,
            datasets: [{
                label: 'Novos Usuários',
                data: values_usuarios,
                fill: true,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.2)',
                tension: 0.2
            }]
        },
        options: {
            responsive: true,
            pointBackgroundColor: '#0d6efd',
            pointRadius: 4,
            plugins: {
                legend: { display: false },
                title: {
                    display: true,
                    text: 'Crescimento de Usuários no Ano Atual',
                    font: { size: 18 }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 5 }
                }
            }
        }
    });
});
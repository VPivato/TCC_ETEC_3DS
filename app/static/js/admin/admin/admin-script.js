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

// GRÁFICO PRODUTOS
const ctxProdutos = document.getElementById('grafico-produtos').getContext('2d');
new Chart(ctxProdutos, {
    type: 'bar',
    data: {
        labels: ['Produto X', 'Produto Y', 'Produto Z', 'Produto W', 'Produto V'],
        datasets: [{
            label: 'Qtd. em Estoque',
            data: [2, 4, 5, 6, 8],
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
const ctx = document.getElementById('grafico-pedidos').getContext('2d');
new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['Semana 1', 'Semana 2', 'Semana 3', 'Semana 4'],
        datasets: [{
            label: 'Pedidos',
            data: [30, 45, 50, 40],
            fill: true,
            borderColor: '#0d6efd',
            backgroundColor: 'rgba(13, 110, 253, 0.2)',
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: { display: false },
            title: {
                display: true,
                text: 'Vendas no Último Mês',
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
            y: {
                min: 0,
                max: 100,
                ticks: {
                    stepSize: 10
                }
            }
        },
        pointBackgroundColor: '#0d6efd',
        pointRadius: 4,
    }
});

// GRÁFICO DE CRESCIMENTO DE USUÁRIOS - BANCO DE DADOS
const ctxUsuarios = document.getElementById('grafico-usuarios').getContext('2d');
new Chart(ctxUsuarios, {
    type: 'line',
    data: {
        labels: ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'],
        datasets: [{
            label: 'Novos Usuários',
            data: [34, 28, 22, 24, 18, 15, 27, 23, 11, 17, 25, 46],
            fill: true,
            borderColor: '#0d6efd',
            backgroundColor: 'rgba(13, 110, 253, 0.2)',
            tension: .2
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
                text: 'Crescimento de Usuários no Último Ano',
                font: { size: 18 }
            }
        },
        scales: {
            y: {
                min: 0,
                ticks: { stepSize: 10 },
            },
        }
    }
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
document.addEventListener("DOMContentLoaded", function () {
    // --- Gráfico Vendas por Dia ---
    const canvasVendas = document.getElementById('graficoVendasDia');
    const labelsVendas = JSON.parse(canvasVendas.dataset.labels);
    const valoresVendas = JSON.parse(canvasVendas.dataset.valores);

    new Chart(canvasVendas.getContext('2d'), {
        type: 'line',
        data: {
            labels: labelsVendas,
            datasets: [{
                label: 'Vendas',
                data: valoresVendas,
                borderColor: '#0d6efd',
                backgroundColor: '#0d6efd33',
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: '' }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    // --- Gráfico Participação por Produto ---
    const canvasProdutos = document.getElementById('graficoProdutos');
    const labelsProdutos = JSON.parse(canvasProdutos.dataset.labels);
    const valoresProdutos = JSON.parse(canvasProdutos.dataset.valores);

    new Chart(canvasProdutos.getContext('2d'), {
        type: 'pie',
        data: {
            labels: labelsProdutos,
            datasets: [{
                data: valoresProdutos,
                backgroundColor: ['#0d6efd', '#198754', '#ffc107', '#dc3545', '#6f42c1']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 20, // largura do quadrado de cor
                        padding: 15    // espaço entre itens
                    }
                }
            }
        }
    });
});
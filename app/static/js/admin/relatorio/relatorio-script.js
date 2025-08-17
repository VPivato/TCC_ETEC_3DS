document.getElementById('btnBuscarProduto').addEventListener('click', function () {
    const produtoBusca = document.getElementById('produtoBusca').value.trim();
    const periodo = document.getElementById('periodo').value;
    const dataInicio = document.getElementById('dataInicio').value;
    const dataFim = document.getElementById('dataFim').value;

    if (!produtoBusca) {
        alert("Digite um nome ou ID de produto.");
        return;
    }

    fetch(`/relatorio/produto`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token() }}'
        },
        body: JSON.stringify({
            produtoBusca,
            periodo,
            dataInicio,
            dataFim
        })
    })
        .then(res => res.json())
        .then(data => {
            if (data.erro) {
                alert(data.erro);
                return;
            }

            // Atualiza painel
            document.getElementById('descricaoProduto').innerHTML = `${data.descricao} #${data.id_prod}`
            document.getElementById('categoriaProduto').innerHTML = data.categ
            document.getElementById('faturamentoProduto').innerHTML =
                `R$ ${data.faturamento.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} <small class="text-success">(${data.variacaoFaturamento}%)</small>`;
            document.getElementById('vendasProduto').textContent = data.vendas;
            document.getElementById('estoqueProduto').textContent = `${data.estoque} unidades`;
            document.getElementById('presenteEm').textContent = `${data.percentualPedidos}% dos pedidos`;
            document.getElementById('participacaoTotal').textContent = `${data.percentualParticipacao}%`;

            // Atualiza gráfico
            if (window.graficoProduto) {
                window.graficoProduto.destroy();
            }
            const ctx = document.getElementById('graficoVendasProduto').getContext('2d');
            window.graficoProduto = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.grafico.labels,
                    datasets: [{
                        label: data.descricao,
                        data: data.grafico.valores,
                        borderColor: '#0d6efd',
                        backgroundColor: 'rgba(13, 110, 253, 0.2)',
                        fill: true
                    }]
                },
                options: {
                    plugins: {
                        legend: { position: '' },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    let valor = context.raw || 0
                                    return 'R$ ' + valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 });
                                }
                            }
                        }
                    },
                }
            });
        });
});

document.getElementById('btnLimparBusca').addEventListener('click', function () {
    // Limpar campos de input
    document.getElementById('produtoBusca').value = '';

    // Resetar informações do produto
    document.getElementById('descricaoProduto').textContent = '--';
    document.getElementById('categoriaProduto').textContent = '--';
    document.getElementById('faturamentoProduto').textContent = 'R$ 0';
    document.getElementById('vendasProduto').textContent = '0';
    document.getElementById('estoqueProduto').textContent = '0 unidades';
    document.getElementById('presenteEm').textContent = '0% dos pedidos';
    document.getElementById('participacaoTotal').textContent = '0%';

    // Resetar gráfico de vendas
    const canvas = document.getElementById('graficoVendasProduto');
    if (window.graficoProduto) {
        window.graficoProduto.destroy(); // destrói gráfico anterior
        window.graficoProduto = null;
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const selectPeriodo = document.getElementById("periodo");
    const camposData = document.querySelectorAll(".campo-data");
    function toggleCamposData() {
        if (selectPeriodo.value === "personalizado") {
            camposData.forEach(campo => campo.style.display = "");
        } else {
            camposData.forEach(campo => campo.style.display = "none");
        }
    }
    // Executa na inicialização (caso já esteja selecionado "personalizado")
    toggleCamposData();
    // Executa sempre que mudar a seleção
    selectPeriodo.addEventListener("change", toggleCamposData);

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
                fill: true,
                tension: 0.3,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: '' },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            let valor = context.raw || 0
                            return 'R$ ' + valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 });
                        }
                    }
                }
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
    if (canvasProdutos) {
        const labelsProdutos = JSON.parse(canvasProdutos.dataset.labels);
        const valoresProdutos = JSON.parse(canvasProdutos.dataset.valores).map(Number);

        new Chart(canvasProdutos.getContext('2d'), {
            type: 'pie',
            data: {
                labels: labelsProdutos,
                datasets: [{
                    data: valoresProdutos,
                    backgroundColor: ['#0d6efd', '#198754', '#ffc107', '#dc3545', '#6f42c1'],
                    hoverOffset: 15
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 20,
                            padding: 15
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                let valor = context.raw || 0;
                                return `${valor} itens`;
                            }
                        }
                    },
                    datalabels: {
                        color: '#fff',
                        font: { weight: 'bold', size: 14 },
                        formatter: (value, context) => {
                            const total = context.chart.data.datasets[0].data
                                .reduce((a, b) => a + b, 0);
                            return ((value / total) * 100).toFixed(1) + '%';
                        }
                    }
                }
            },
            plugins: [ChartDataLabels]
        });
    }

    // Gráfico de barras - produtos com estoque baixo
    const ctxBar = document.getElementById('graficoEstoqueBaixo');
    if (ctxBar) {
        const labels = JSON.parse(ctxBar.dataset.labels);
        const valores = JSON.parse(ctxBar.dataset.valores);

        new Chart(ctxBar.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Estoque',
                    data: valores,
                    backgroundColor: 'rgba(255, 99, 132, 0.6)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1,
                }]
            },
            options: {
                scales: {
                    y: { beginAtZero: true, max: 10 }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    // Gráfico donut - vendas por categoria
    const ctxDonut = document.getElementById('graficoVendasCategoria');
    if (ctxDonut) {
        const labels = JSON.parse(ctxDonut.dataset.labels);
        const valores = JSON.parse(ctxDonut.dataset.valores).map(Number); // garante que são números
        const colors = ['#36A2EB', '#FFCE56', '#FF6384'];

        new Chart(ctxDonut.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: valores,
                    backgroundColor: colors,
                    hoverOffset: 15
                }]
            },
            options: {
                plugins: {
                    legend: { position: 'right' },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                let valor = context.raw || 0;
                                return `${valor.toLocaleString('pt-BR', {
                                    style: 'currency',
                                    currency: 'BRL'
                                })}`;
                            }
                        }
                    },
                    datalabels: {
                        color: '#fff',
                        font: { weight: 'bold', size: 14 },
                        formatter: (value, context) => {
                            const total = context.chart.data.datasets[0].data
                                .reduce((a, b) => a + b, 0);
                            return ((value / total) * 100).toFixed(1) + '%';
                        }
                    }
                }
            },
            plugins: [ChartDataLabels]
        });
    }


    const graficoEl = document.getElementById('graficoCrescimentoClientes');
    const labels = JSON.parse(graficoEl.dataset.labels);
    const valores = JSON.parse(graficoEl.dataset.valores).map(Number);
    const valorMaximo = Math.max(5, Math.max(...valores));
    new Chart(graficoEl, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Novos Clientes',
                data: valores,
                borderColor: '#4e73df',
                backgroundColor: 'rgba(78, 115, 223, 0.1)',
                fill: true,
                tension: 0.3,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    min: 0,
                    max: valorMaximo,
                    ticks: {
                        callback: function (value) {
                            return Number.isInteger(value) ? value : '';
                        }
                    },
                    title: { display: true, text: 'Clientes' }
                },
                x: {
                    title: { display: true, text: 'Dia' }
                }
            }
        }
    });


    const ctxDonutPedidos = document.getElementById('graficoStatusPedidos');
    if (ctxDonutPedidos) {
        const labels = JSON.parse(ctxDonutPedidos.dataset.labels);
        const valores = JSON.parse(ctxDonutPedidos.dataset.valores).map(Number);
        const colors = ['#4e73df', '#1cc88a', '#e74a3b']; // azul, verde, vermelho

        new Chart(ctxDonutPedidos.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: valores,
                    backgroundColor: colors,
                    hoverOffset: 15
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'right' },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                let valor = context.raw || 0;
                                return `${valor} pedidos`;
                            }
                        }
                    },
                    datalabels: {
                        color: '#fff',
                        font: { weight: 'bold', size: 14 },
                        formatter: (value, context) => {
                            const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                            return ((value / total) * 100).toFixed(1) + '%';
                        }
                    }
                }
            },
            plugins: [ChartDataLabels]
        });
    }


    // --- Gráfico de Distribuição por Tipo (Pizza) ---
    const tipoCanvas = document.getElementById('grafico-feedback-tipo');
    const tipoLabels = JSON.parse(tipoCanvas.dataset.labels.replace(/'/g, '"'));
    const tipoValores = JSON.parse(tipoCanvas.dataset.valores.replace(/'/g, '"'));

    new Chart(tipoCanvas, {
        type: 'pie',
        data: {
            labels: tipoLabels,
            datasets: [{
                data: tipoValores,
                backgroundColor: ['#0dcaf0', '#dc3545', '#198754', '#ffc107'],
                hoverOffset: 15
            }]
        },
        options: {
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const valor = context.raw;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const perc = ((valor / total) * 100).toFixed(1);
                            return `${valor} (${perc}%)`;
                        }
                    }
                },
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 20,
                        padding: 15
                    }
                },
                datalabels: {
                    color: '#fff',
                    formatter: (value, ctx) => {
                        const data = ctx.chart.data.datasets[0].data;
                        const total = data.reduce((a, b) => a + b, 0);
                        const perc = ((value / total) * 100).toFixed(1);
                        return `${perc}%`;
                    },
                    font: {
                        weight: 'bold',
                        size: 14
                    }
                }
            }
        },
        plugins: [ChartDataLabels]
    });

    // --- Gráfico de Evolução ao Longo do Tempo (Linha) ---
    const tempoCanvas = document.getElementById('grafico-feedback-tempo');
    const tempoLabels = JSON.parse(tempoCanvas.dataset.labels.replace(/'/g, '"'));
    const tempoValores = JSON.parse(tempoCanvas.dataset.valores.replace(/'/g, '"'));

    new Chart(tempoCanvas, {
        type: 'line',
        data: {
            labels: tempoLabels,
            datasets: [{
                label: 'Feedbacks por Dia',
                data: tempoValores,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13,110,253,0.2)',
                fill: true,
                tension: 0.3,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return `${context.raw} feedback(s)`;
                        }
                    }
                },
                legend: {
                    display: false
                }
            },
            scales: {
                x: { title: { display: true, text: 'Data' } },
                y: { title: { display: true, text: 'Quantidade' }, beginAtZero: true, precision: 0 }
            },
            responsive: true,
            maintainAspectRatio: false
        }
    });
});
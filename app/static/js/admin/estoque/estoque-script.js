document.getElementById('filtro-produtos').addEventListener('input', function () {
    const filtro = this.value.toLowerCase();
    const tabela = document.getElementById('tabela-todos-produtos').getElementsByTagName('tr');

    for (let i = 0; i < tabela.length; i++) {
        const cells = tabela[i].getElementsByTagName('td');
        if (cells.length > 0) {
            const id = cells[0].textContent.toLowerCase();
            const nome = cells[1].textContent.toLowerCase();

            if (id.includes(filtro) || nome.includes(filtro)) {
                tabela[i].style.display = '';
            } else {
                tabela[i].style.display = 'none';
            }
        }
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const canvas = document.getElementById("graficoEstoqueBaixo");
    if (!canvas) return;

    // Lê os atributos data-* do canvas
    let labels = canvas.dataset.labels;
    let valores = canvas.dataset.valores;

    // Se vier em formato string do Jinja, converter para array
    try {
        labels = JSON.parse(labels.replace(/'/g, '"'));
        valores = JSON.parse(valores.replace(/'/g, '"'));
    } catch (e) {
        console.error("Erro ao converter dados do gráfico:", e);
        labels = [];
        valores = [];
    }

    const ctx = canvas.getContext("2d");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Estoque",
                data: valores,
                borderWidth: 1,
                backgroundColor: "rgba(54, 162, 235, 0.6)",
                borderColor: "rgba(54, 162, 235, 1)",
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return ` ${context.parsed.y} unidades`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
});

document.querySelectorAll('.btn-repor').forEach(btn => {
    btn.addEventListener('click', () => {
        const produtoId = btn.dataset.id;
        const produtoNome = btn.dataset.nome;

        document.getElementById('produto-id').value = produtoId;
        document.getElementById('modalReporEstoqueLabel').textContent = `Repor Estoque: ${produtoNome}`;
        document.getElementById('quantidade-repor').value = 1;
        document.getElementById('feedback-repor').classList.add('d-none');

        const modal = new bootstrap.Modal(document.getElementById('modalReporEstoque'));
        modal.show();
    });
});

// Envio do formulário
document.getElementById('form-repor-estoque').addEventListener('submit', async (e) => {
    e.preventDefault();

    const produtoId = document.getElementById('produto-id').value;
    const quantidade = document.getElementById('quantidade-repor').value;

    try {
        const response = await fetch('/estoque/repor', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ produto_id: produtoId, quantidade: quantidade })
        });

        const data = await response.json();

        if (data.success) {
            document.getElementById('feedback-repor').textContent = `Estoque atualizado com sucesso!`;
            document.getElementById('feedback-repor').classList.remove('d-none');

            // Atualiza a tabela
            setTimeout(() => window.location.reload(), 1000);
        } else {
            document.getElementById('feedback-repor').textContent = `Erro: ${data.message}`;
            document.getElementById('feedback-repor').classList.remove('d-none');
        }
    } catch (err) {
        document.getElementById('feedback-repor').textContent = `Erro ao atualizar o estoque.`;
        document.getElementById('feedback-repor').classList.remove('d-none');
    }
});

if (localStorage.getItem('modo-escuro') === 'true') {
    document.body.classList.add('modo-escuro')
}
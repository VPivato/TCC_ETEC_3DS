let checkboxVisiveis = false

function carregarColunas(modelo) {
    fetch('/database/get_colunas', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ modelo: modelo })
    })
        .then(response => response.json())
        .then(data => {
            const colunaSelect = document.getElementById('coluna-select')
            colunaSelect.innerHTML = ''
            data.forEach(coluna => {
                const option = document.createElement('option')
                option.value = coluna
                option.textContent = coluna
                colunaSelect.appendChild(option)
            })
        })
}

function carregarTabela(modelo, checkboxVisiveis = false) {
    fetch('/database/get_registros', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ modelo: modelo })
    })
        .then(response => response.json())
        .then(data => {
            const head = document.getElementById('table-head')
            const body = document.getElementById('table-body')

            head.innerHTML = ''
            body.innerHTML = ''

            if (data.erro) {
                head.innerHTML = '<tr><th>Erro</th></tr>'
                body.innerHTML = `<tr><td>${data.erro}</td></tr>`
                return
            }

            // Cabeçalhos + coluna de ação
            const headerRow = document.createElement('tr')
            const thCheckbox = document.createElement('th');
            thCheckbox.classList.add('col-checkbox');
            thCheckbox.textContent = ''; // sem título
            if (!checkboxVisiveis) {
                thCheckbox.style.display = "none"
            }
            else {
                thCheckbox.style.display = ""
            }
            headerRow.appendChild(thCheckbox);
            data.colunas.forEach(col => {
                const th = document.createElement('th')
                th.textContent = col
                headerRow.appendChild(th)
            })
            const thAcao = document.createElement('th')
            thAcao.textContent = 'Ação'
            headerRow.appendChild(thAcao)
            head.appendChild(headerRow)

            // Registros
            data.registros.forEach(registro => {
                const row = document.createElement('tr')

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.classList.add('selecionar-registro');
                checkbox.value = registro.id;

                const tdCheckbox = document.createElement('td');
                tdCheckbox.classList.add('col-checkbox');
                if (!checkboxVisiveis) {
                    tdCheckbox.style.display = 'none'
                }
                else {
                    tdCheckbox.style.display = ''
                }
                tdCheckbox.appendChild(checkbox);
                row.appendChild(tdCheckbox);

                data.colunas.forEach(col => {
                    const td = document.createElement('td')
                    td.textContent = registro[col]
                    row.appendChild(td)
                })

                // Botão excluir
                const tdAcao = document.createElement('td')
                const btnExcluir = document.createElement('button')
                btnExcluir.textContent = 'Excluir'
                btnExcluir.classList.add('btn-excluir')
                btnExcluir.onclick = () => {
                    if (confirm(`Excluir o registro #${registro.id}?`)) {
                        fetch(`/database/excluir/${modelo}/${registro.id}`, {
                            method: 'POST'
                        })
                            .then(res => res.json())
                            .then(response => {
                                if (response.sucesso) {
                                    carregarTabela(modelo, checkboxVisiveis) // Recarrega a tabela
                                } else {
                                    alert(response.erro)
                                }
                            })
                    }
                }
                tdAcao.appendChild(btnExcluir)
                row.appendChild(tdAcao)

                body.appendChild(row)
            })
        })
}

document.getElementById('select-tabela').addEventListener('change', function () {
    carregarColunas(this.value)
    carregarTabela(this.value, checkboxVisiveis)
    document.getElementById("valor-consulta").type = "text"
})

document.getElementById("coluna-select").addEventListener("change", function () {
    if (this.value.includes("data")) {
        document.getElementById("valor-consulta").type = "date"
    }
    else {
        document.getElementById("valor-consulta").type = "text"
    }
})

document.getElementById("consulta-form").addEventListener("submit", e => {
    e.preventDefault()
    const modelo = document.getElementById('select-tabela').value;
    const coluna = document.getElementById('coluna-select').value;
    const operador = document.getElementById('operador-select').value;
    const valor = document.getElementById('valor-consulta').value;

    fetch('/database/filtrar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ modelo, coluna, operador, valor })
    })
        .then(res => res.json())
        .then(data => {
            const head = document.getElementById('table-head');
            const body = document.getElementById('table-body');
            head.innerHTML = '';
            body.innerHTML = '';

            if (data.erro) {
                head.innerHTML = '<tr><th>Erro</th></tr>';
                body.innerHTML = `<tr><td>${data.erro}</td></tr>`;
                return;
            }

            const headerRow = document.createElement('tr');
            const thCheckbox = document.createElement('th');
            thCheckbox.classList.add('col-checkbox');
            thCheckbox.textContent = ''; // sem título
            thCheckbox.style.display = "none"
            headerRow.appendChild(thCheckbox);

            data.colunas.forEach(col => {
                const th = document.createElement('th');
                th.textContent = col;
                headerRow.appendChild(th);
            });
            const thAcao = document.createElement('th')
            thAcao.textContent = 'Ação'
            headerRow.appendChild(thAcao)
            head.appendChild(headerRow);

            data.registros.forEach(reg => {
                const row = document.createElement('tr');

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.classList.add('selecionar-registro');
                if (!checkboxVisiveis) {
                    checkbox.style.display = 'none'
                }
                else {
                    checkbox.style.display = ''
                }
                checkbox.value = reg.id;

                const tdCheckbox = document.createElement('td');
                tdCheckbox.classList.add('col-checkbox');
                tdCheckbox.style.display = 'none'
                tdCheckbox.appendChild(checkbox);
                row.appendChild(tdCheckbox);

                data.colunas.forEach(col => {
                    const td = document.createElement('td');
                    td.textContent = reg[col];
                    row.appendChild(td);
                });
                const tdAcao = document.createElement('td')
                const btnExcluir = document.createElement('button')
                btnExcluir.textContent = 'Excluir'
                btnExcluir.onclick = () => {
                    if (confirm(`Excluir o registro #${reg.id}?`)) {
                        fetch(`/database/excluir/${modelo}/${reg.id}`, {
                            method: 'POST'
                        })
                            .then(res => res.json())
                            .then(response => {
                                if (response.sucesso) {
                                    carregarTabela(modelo, checkboxVisiveis) // Recarrega a tabela
                                } else {
                                    alert(response.erro)
                                }
                            })
                    }
                }
                tdAcao.appendChild(btnExcluir)
                row.appendChild(tdAcao)
                body.appendChild(row)
            });
        });
})

document.getElementById("limpar").addEventListener("click", () => {
    let tabela = document.getElementById('select-tabela')
    const modelo = tabela.value;

    document.getElementById('valor-consulta').value = '';
    document.getElementById('operador-select').value = '=';

    carregarTabela(modelo, checkboxVisiveis)
})

document.getElementById('toggle-excluir-varios').addEventListener('change', function () {
    if (this.checked) {
        document.querySelectorAll('.col-checkbox').forEach(el => el.style.display = '');
        document.querySelectorAll('.selecionar-registro').forEach(cb => cb.style.display = '');
        checkboxVisiveis = true
    }
    else {
        document.querySelectorAll('.col-checkbox').forEach(el => el.style.display = 'none');
        document.querySelectorAll('.selecionar-registro').forEach(cb => {
            cb.style.display = 'none'
            cb.checked = false
        });
        checkboxVisiveis = false
    }
});

document.getElementById('excluir-varios').addEventListener("click", (e) => {
    e.preventDefault()
    const modelo = document.getElementById('select-tabela').value;
    const selecionados = Array.from(document.querySelectorAll('.selecionar-registro:checked'))
        .map(cb => parseInt(cb.value));

    if (selecionados.length === 0) {
        alert("Selecione pelo menos um registro.");
        return;
    }

    if (!confirm(`Deseja excluir ${selecionados.length} registro(s)?`)) return;

    fetch('/database/excluir_varios', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ modelo, ids: selecionados })
    })
        .then(res => res.json())
        .then(data => {
            if (data.sucesso) {
                alert(data.mensagem);
                carregarTabela(modelo, checkboxVisiveis); // recarrega a tabela
            } else {
                alert(data.erro || "Erro desconhecido.");
            }

            document.getElementById('cancelar-selecao').click();
        });
})

document.getElementById("cancelar-selecao").addEventListener('click', () => {
    Array.from(document.querySelectorAll('.selecionar-registro:checked')).map(el => el.checked = false)
})

if (localStorage.getItem('modo-escuro') === 'true') {
    document.body.classList.add('modo-escuro')
}

document.getElementById('select-tabela').dispatchEvent(new Event('change'))
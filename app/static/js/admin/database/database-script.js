// database-script.js
// USO: espera elementos com IDs existentes no seu template.
// Faz chamadas POST para /database/get_registros e /database/filtrar com {modelo, page, per_page, ...}

document.addEventListener('DOMContentLoaded', () => {
    // Estado
    let currentModelo = document.getElementById('select-tabela').value;
    let currentPage = 1;
    let perPage = parseInt(document.getElementById('per-page').value, 10) || 25;
    let currentFilter = null; // {coluna, operador, valor} ou null
    let checkboxVisiveis = false;

    // Elementos
    const colunaSelect = document.getElementById('coluna-select');
    const tableHead = document.getElementById('table-head');
    const tableBody = document.getElementById('table-body');
    const pageInfo = document.getElementById('page-info');
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    const firstBtn = document.getElementById('first-page');
    const lastBtn = document.getElementById('last-page');
    const perPageSelect = document.getElementById('per-page');
    const toggleExcluir = document.getElementById('toggle-excluir-varios');

    // Helper fetch wrapper
    async function postJson(url, payload) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return res.json();
    }

    // Carrega colunas do modelo selecionado
    async function carregarColunas(modelo) {
        const data = await postJson('/database/get_colunas', { modelo });
        colunaSelect.innerHTML = '';
        if (data && Array.isArray(data)) {
            data.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c;
                opt.textContent = c;
                colunaSelect.appendChild(opt);
            });
        } else if (data && data.erro) {
            colunaSelect.innerHTML = `<option value="">${data.erro}</option>`;
        }
    }

    // Renderiza tabela dados e controles de paginação
    function renderTabela(data) {
        tableHead.innerHTML = '';
        tableBody.innerHTML = '';

        if (!data || data.erro) {
            const headerRow = document.createElement('tr');
            headerRow.innerHTML = `<th>Erro</th>`;
            tableHead.appendChild(headerRow);
            const bodyRow = document.createElement('tr');
            bodyRow.innerHTML = `<td>${data ? data.erro : 'Erro desconhecido'}</td>`;
            tableBody.appendChild(bodyRow);
            pageInfo.textContent = '';
            prevBtn.disabled = nextBtn.disabled = firstBtn.disabled = lastBtn.disabled = true;
            return;
        }

        // Cabeçalho: checkbox (se ativo), colunas, ação
        const headerRow = document.createElement('tr');
        // checkbox col
        const thCheckbox = document.createElement('th');
        thCheckbox.classList.add('col-checkbox');
        if (!checkboxVisiveis) thCheckbox.style.display = 'none';
        headerRow.appendChild(thCheckbox);

        data.colunas.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            headerRow.appendChild(th);
        });

        const thAcao = document.createElement('th');
        thAcao.textContent = 'Ação';
        headerRow.appendChild(thAcao);
        tableHead.appendChild(headerRow);

        // Registros
        data.registros.forEach(reg => {
            const tr = document.createElement('tr');

            // checkbox cell
            const tdChk = document.createElement('td');
            tdChk.classList.add('col-checkbox');
            if (!checkboxVisiveis) tdChk.style.display = 'none';
            const chk = document.createElement('input');
            chk.type = 'checkbox';
            chk.classList.add('selecionar-registro');
            chk.value = reg.id; // supondo que todo modelo tenha id
            tdChk.appendChild(chk);
            tr.appendChild(tdChk);

            // outras colunas
            data.colunas.forEach(col => {
                const td = document.createElement('td');
                let val = reg[col];
                // formatar datas legíveis (se vierem como ISO string)
                if (val && typeof val === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(val)) {
                    try { val = new Date(val).toLocaleString(); } catch (e) { }
                }
                td.textContent = (val === null || val === undefined) ? '' : val;
                tr.appendChild(td);
            });

            // ação: excluir (mantém comportamento atual)
            const tdAcao = document.createElement('td');
            const btnExcluir = document.createElement('button');
            btnExcluir.type = 'button';
            btnExcluir.className = 'btn btn-sm btn-outline-danger btn-excluir';
            btnExcluir.textContent = 'Excluir';
            btnExcluir.addEventListener('click', () => excluirRegistro(currentModelo, reg.id));
            tdAcao.appendChild(btnExcluir);
            tr.appendChild(tdAcao);

            tableBody.appendChild(tr);
        });

        // Paginação UI
        currentPage = data.page;
        pageInfo.textContent = `Página ${data.page} de ${data.pages} • ${data.total} registros`;
        prevBtn.disabled = !data.page || data.page <= 1;
        firstBtn.disabled = prevBtn.disabled;
        nextBtn.disabled = !data.page || data.page >= data.pages;
        lastBtn.disabled = nextBtn.disabled;
    }

    // Carrega dados (com ou sem filtro)
    async function carregarTabela(page = 1) {
        const payload = {
            modelo: currentModelo,
            page: page,
            per_page: perPage
        };

        let data;
        if (currentFilter) {
            Object.assign(payload, currentFilter);
            data = await postJson('/database/filtrar', payload);
        } else {
            data = await postJson('/database/get_registros', payload);
        }

        renderTabela(data);
    }

    // Exclusão única
    async function excluirRegistro(modelo, id) {
        const ok = await Swal.fire({
            title: `Excluir registro #${id}?`,
            text: 'A ação não poderá ser desfeita.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Sim, excluir',
            cancelButtonText: 'Cancelar'
        }).then(r => r.isConfirmed);

        if (!ok) return;

        const res = await fetch(`/database/excluir/${modelo}/${id}`, { method: 'POST' });
        const data = await res.json();
        if (data.sucesso) {
            Swal.fire({ icon: 'success', title: 'Excluído', timer: 1200, showConfirmButton: false });
            carregarTabela(currentPage);
        } else {
            Swal.fire({ icon: 'error', title: 'Erro', text: data.erro || 'Não foi possível excluir' });
        }
    }

    // Excluir vários já existe: apenas reusa a função carregarTabela para recarregar a página atual.

    // Eventos de paginação
    prevBtn.addEventListener('click', () => carregarTabela(Math.max(1, currentPage - 1)));
    nextBtn.addEventListener('click', () => carregarTabela(currentPage + 1));
    firstBtn.addEventListener('click', () => carregarTabela(1));
    lastBtn.addEventListener('click', async () => {
        // para saber última página precisamos buscar com page=1 (ou confiar na pageInfo).
        // Chamamos servidor pedindo página atual para encontrar pages.
        const payload = { modelo: currentModelo, page: 1, per_page: perPage };
        const data = currentFilter ? await postJson('/database/filtrar', Object.assign({}, payload, currentFilter)) : await postJson('/database/get_registros', payload);
        if (data && data.pages) {
            carregarTabela(data.pages);
        }
    });

    // change per_page
    perPageSelect.addEventListener('change', () => {
        perPage = parseInt(perPageSelect.value, 10) || 25;
        carregarTabela(1);
    });

    // mudança de tabela
    document.getElementById('select-tabela').addEventListener('change', async (e) => {
        currentModelo = e.target.value;
        currentPage = 1;
        currentFilter = null;
        checkboxVisiveis = false;
        toggleExcluir.checked = false;
        await carregarColunas(currentModelo);
        carregarTabela(1);
    });

    // mudança de coluna (altera tipo do input)
    colunaSelect.addEventListener('change', (e) => {
        const val = e.target.value || '';
        const input = document.getElementById('valor-consulta');
        if (val.toLowerCase().includes('data')) input.type = 'date';
        else input.type = 'text';
    });

    // submit do filtro
    document.getElementById('consulta-form').addEventListener('submit', async (ev) => {
        ev.preventDefault();
        const coluna = document.getElementById('coluna-select').value;
        const operador = document.getElementById('operador-select').value;
        const valor = document.getElementById('valor-consulta').value;

        if (!coluna || !operador) {
            Swal.fire({ icon: 'warning', title: 'Defina coluna e operador' });
            return;
        }

        // salva filtro e carrega página 1
        currentFilter = { coluna, operador, valor };
        carregarTabela(1);
    });

    // limpar filtro
    document.getElementById('limpar').addEventListener('click', () => {
        currentFilter = null;
        document.getElementById('valor-consulta').value = '';
        document.getElementById('operador-select').value = '=';
        carregarTabela(1);
    });

    // toggle seleção múltipla
    toggleExcluir.addEventListener('change', (e) => {
        checkboxVisiveis = e.target.checked;
        // redesenhar tabela na página atual para refletir checkboxes
        carregarTabela(currentPage);
    });

    // excluir varios
    document.getElementById('excluir-varios').addEventListener('click', async (ev) => {
        ev.preventDefault();
        const modelo = currentModelo;
        const selecionados = Array.from(document.querySelectorAll('.selecionar-registro:checked')).map(cb => parseInt(cb.value));
        if (!selecionados.length) {
            Swal.fire({ icon: 'warning', title: 'Nada selecionado', text: 'Selecione registros para excluir.' });
            return;
        }

        const confirmado = await Swal.fire({
            title: `Excluir ${selecionados.length} registros?`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Sim, excluir'
        }).then(r => r.isConfirmed);

        if (!confirmado) return;

        const res = await fetch('/database/excluir_varios', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ modelo, ids: selecionados })
        });
        const data = await res.json();
        if (data.sucesso) {
            Swal.fire({ icon: 'success', title: data.mensagem, toast: true, position: 'bottom-end', timer: 2000, showConfirmButton: false });
            carregarTabela(currentPage);
            // esconder seleção
            document.getElementById('cancelar-selecao').click();
        } else {
            Swal.fire({ icon: 'error', title: 'Erro', text: data.erro || 'Não foi possível excluir' });
        }
    });

    // cancelar seleção
    document.getElementById('cancelar-selecao').addEventListener('click', () => {
        document.querySelectorAll('.selecionar-registro').forEach(cb => { cb.checked = false; });
        if (document.getElementById('toggle-excluir-varios').checked) {
            document.getElementById('toggle-excluir-varios').checked = false;
            checkboxVisiveis = false;
            carregarTabela(currentPage);
        }
    });

    // inicialização
    (async () => {
        await carregarColunas(currentModelo);
        carregarTabela(1);
    })();
});
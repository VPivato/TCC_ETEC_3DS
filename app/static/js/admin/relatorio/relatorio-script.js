document.getElementById("btnFiltrar").addEventListener("click", function () {
    const dataInicio = document.getElementById("dataInicio").value;
    const dataFim = document.getElementById("dataFim").value;

    if (!dataInicio || !dataFim) {
        alert("Selecione ambas as datas para filtrar.");
        return;
    }

    console.log("Filtrando de", dataInicio, "até", dataFim);
    // Aqui você chama sua rota Flask passando essas datas como parâmetros
    // e atualiza as seções ativas
});

document.getElementById("btnLimparFiltro").addEventListener("click", function () {
    document.getElementById("dataInicio").value = "";
    document.getElementById("dataFim").value = "";
    console.log("Filtro limpo");
    // Aqui você recarrega os dados sem filtro
});

document.addEventListener('DOMContentLoaded', function () {
    const selectPeriodo = document.getElementById('periodo');
    const camposData = document.querySelectorAll('.campo-data');

    // Função para alternar visibilidade
    function atualizarCamposData() {
        if (selectPeriodo.value === 'personalizado') {
            camposData.forEach(campo => campo.style.display = 'block');
        } else {
            camposData.forEach(campo => campo.style.display = 'none');
        }
    }

    // Evento para mudança no select
    selectPeriodo.addEventListener('change', atualizarCamposData);

    // Inicializa o estado correto
    atualizarCamposData();
})
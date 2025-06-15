function confirmarFinalizacao(pedidoId) {
    Swal.fire({
        title: 'Tem certeza?',
        text: "Deseja marcar o pedido #" + pedidoId + " como retirado?",
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#28a745',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Sim, confirmar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = "/pedido/finalizar/" + pedidoId;
        }
    });
}

function confirmarCancelamento(pedidoId) {
    Swal.fire({
        title: 'Tem certeza?',
        text: "Deseja cancelar o pedido #" + pedidoId + "? Essa ação não pode ser desfeita.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Sim, cancelar pedido',
        cancelButtonText: 'Voltar'
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = "/pedido/cancelar/" + pedidoId;
        }
    });
}

// Toast após redirecionamento
document.addEventListener('DOMContentLoaded', function () {
    // 1) Toast
    const params = new URLSearchParams(window.location.search);
    const toast = params.get('toast');
    if (toast) {
        Swal.fire({
            toast: true,
            position: 'bottom-end',
            icon: 'success',
            title: toast,
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true
        });
        // limpar ?toast=…
        const newUrl = window.location.origin + window.location.pathname +
            window.location.search.replace(/([&?])toast=[^&]+(&|$)/, '$1')
                .replace(/(&|\?)$/, '');
        window.history.replaceState({}, document.title, newUrl);
    }

    // 2) Collapse header
    document.querySelectorAll('.collapse.pedido-body').forEach(p => {
        const id = p.id.replace('pedido', ''),
            info = document.getElementById('info-header-' + id);
        p.addEventListener('show.bs.collapse', () => info.classList.add('show'));
        p.addEventListener('hide.bs.collapse', () => info.classList.remove('show'));
    });
});
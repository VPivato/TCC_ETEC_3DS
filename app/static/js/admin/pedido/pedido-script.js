function confirmarFinalizacao(pedidoId) {
    Swal.fire({
        title: 'Tem certeza?',
        text: "Deseja marcar o pedido #" + pedidoId + " como retirado?",
        icon: 'warning',
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
    const urlParams = new URLSearchParams(window.location.search);
    const toastMessage = urlParams.get('toast');

    if (toastMessage) {
        Swal.fire({
            toast: true,
            position: 'bottom-end',
            icon: 'success',
            title: toastMessage,
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true
        });

        // Remove o ?toast= da URL após exibir
        const newUrl = window.location.origin + window.location.pathname +
            window.location.search.replace(/([&?])toast=[^&]+(&|$)/, '$1')
                .replace(/(&|\?)$/, '');
        window.history.replaceState({}, document.title, newUrl);
    }
});
document.querySelectorAll('.btn-editar').forEach(button => {
    const form = document.getElementById('form-editar');
    button.addEventListener('click', function () {
        const id = this.getAttribute('data-id');
        const mensagem = this.getAttribute('data-mensagem');
        const data = this.getAttribute('data-data');

        // Preenche os campos do modal
        document.getElementById('editar-id').value = id;
        document.getElementById('editar-mensagem').value = mensagem;
        document.getElementById('editar-data').value = data;

        // Define a ação do form dinamicamente
        form.action = `/notificacao/editar/${id}`;
    });
});

// CONFIRMAÇÃO ENVIAR NOTIFICAÇÃO
document.getElementById('form-notificacao').addEventListener('submit', function (e) {
    e.preventDefault()
    Swal.fire({
        title: 'Enviar notificação?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#198754',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Sim, enviar',
        cancelButtonText: 'Não, voltar'
    }).then((result) => {
        if (result.isConfirmed) {
            e.target.submit()
        }
        else {
            window.location.href = ""
        }
    })
})

// CONFIRMAÇÃO EXCLUIR NOTIFICAÇÃO
document.querySelectorAll('.form-excluir').forEach(form => {
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        Swal.fire({
            title: 'Excluir notificação?',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            confirmButtonText: 'Sim, excluir',
            cancelButtonText: 'Não, voltar'
        }).then((result) => {
            if (result.isConfirmed) {
                form.submit();
            }
        });
    });
});


if (localStorage.getItem('modo-escuro') === 'true') {
    document.body.classList.add('modo-escuro')
}
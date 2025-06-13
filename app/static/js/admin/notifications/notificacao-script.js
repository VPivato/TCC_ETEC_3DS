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

if (localStorage.getItem('modo-escuro') === 'true') {
    document.body.classList.add('modo-escuro')
}
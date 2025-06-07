function previewImagem() {
    const input = document.getElementById('imagem');
    const preview = document.getElementById('preview');

    const file = input.files[0];
    if (file) {
        const reader = new FileReader();

        reader.onload = function (e) {
            preview.src = e.target.result;
        }

        reader.readAsDataURL(file);
    } else {
        preview.src = "/static/uploads/default.png"
    }
}

function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1).toLowerCase();
}

document.getElementById("cancelar").addEventListener("click", () => {
    const preview = document.getElementById('preview');
    preview.src = "/static/uploads/default.png"
})

document.getElementById("preview").addEventListener("click", () => {
    document.getElementById('imagem').click()
})

document.querySelectorAll('.btn-editar').forEach(button => {
    const form = document.getElementById('form-editar');
    button.addEventListener('click', function () {
        const id = this.getAttribute('data-id');
        const descricao = this.getAttribute('data-descricao');
        const categoria = this.getAttribute('data-categoria');
        const preco = this.getAttribute('data-preco');
        const estoque = this.getAttribute('data-estoque');
        const imagem = this.getAttribute('data-imagem');

        // Preenche os campos do modal
        document.getElementById('editar-id').value = id;
        document.getElementById('editar-descricao').value = descricao;
        document.getElementById('editar-categoria').value = capitalize(categoria);
        document.getElementById('editar-preco').value = preco;
        document.getElementById('editar-estoque').value = estoque;

        // Define a ação do form dinamicamente
        form.action = `/produto/editar/${id}`;
    });
});
function previewImagem() {
    const input = document.getElementById('imagem');
    const preview = document.getElementById('preview-cadastro');

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
    const preview = document.getElementById('preview-cadastro');
    preview.src = "/static/uploads/default.png"
})

document.getElementById("preview-cadastro").addEventListener("click", () => {
    document.getElementById('imagem').click()
})

const inputImagem = document.getElementById('editar-imagem');
const imagemPreview = document.getElementById('preview-modal');
inputImagem.addEventListener('change', function () {
    const file = this.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            imagemPreview.src = e.target.result;
        };
        reader.readAsDataURL(file);
    } else {
        imagemPreview.src = '';
        imagemPreview.style.display = 'none';
    }
});
imagemPreview.addEventListener('click', () => {
    inputImagem.click()
})
document.getElementById('modalEditar').addEventListener('hidden.bs.modal', () => {
    imagemPreview.src = '';
    inputImagem.value = ''; // limpa o input
});

document.querySelectorAll('.btn-editar').forEach(button => {
    const form = document.getElementById('form-editar');
    button.addEventListener('click', function () {
        const id = this.getAttribute('data-id');
        const descricao = this.getAttribute('data-descricao');
        const categoria = this.getAttribute('data-categoria');
        const preco = this.getAttribute('data-preco');
        const estoque = this.getAttribute('data-estoque');
        const imagem = this.getAttribute('data-imagem');

        const imagemPreview = document.getElementById('preview-modal');
        if (imagem && imagem !== 'None') {
            imagemPreview.src = `/static/${imagem}`;
        } else {
            imagemPreview.src = '';
            imagemPreview.style.display = 'none';
        }


        // Preenche os campos do modal
        document.getElementById('editar-id').value = id;
        document.getElementById('editar-descricao').value = descricao;
        document.getElementById('editar-categoria').value = capitalize(categoria);
        document.getElementById('editar-preco').value = preco;
        document.getElementById('editar-estoque').value = estoque;
        // document.getElementById('preview-modal').src = ;

        // Define a ação do form dinamicamente
        form.action = `/produto/editar/${id}`;
    });
});

// --- CONFIRMAÇÃO DE EXCLUSÃO ---
document.querySelectorAll('.form-excluir').forEach(form => {
    form.addEventListener('submit', function (e) {
        e.preventDefault(); // impede envio imediato

        Swal.fire({
            title: 'Excluir produto?',
            text: 'Essa ação não poderá ser desfeita!',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Sim, excluir',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                form.submit(); // só envia após confirmação
            }
        });
    });
});

// --- CADASTRO DE PRODUTO ---
const formCadastro = document.getElementById('form-cadastro-produto');
if (formCadastro) {
    formCadastro.addEventListener('submit', function (e) {
        e.preventDefault(); // impede envio imediato

        Swal.fire({
            title: 'Cadastrar produto?',
            text: 'Deseja confirmar o cadastro deste produto?',
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#198754',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Sim, cadastrar',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                formCadastro.submit(); // envia se confirmado
            }
        });
    });
}

if (localStorage.getItem('modo-escuro') === 'true') {
    document.body.classList.add('modo-escuro')
}
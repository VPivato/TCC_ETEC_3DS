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

document.getElementById("cancelar").addEventListener("click", () => {
    const preview = document.getElementById('preview');
    preview.src = "/static/uploads/default.png"
})

document.getElementById("preview").addEventListener("click", () => {
    document.getElementById('imagem').click()
})
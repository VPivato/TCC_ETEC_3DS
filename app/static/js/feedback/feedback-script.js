const textarea_feedback = document.querySelector("#texto_feedback")
const contador_feedback = document.querySelector("#contador")
const tamanho_maximo = 300

textarea_feedback.addEventListener("input", () => {
    restante = tamanho_maximo - textarea_feedback.value.length
    contador_feedback.innerHTML = restante
})

document.getElementById('form-feedback').addEventListener('submit', function (e) {
    e.preventDefault();

    Swal.fire({
        title: 'Confirmar o envio da mensagem?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#198754',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Sim, enviar',
        cancelButtonText: 'Cancelar',
    }).then((result) => {
        if (result.isConfirmed) {
            const formData = new FormData(e.target);

            fetch('/feedback/enviar_feedback', {
                method: 'POST',
                body: formData,
            })
                .then(response => {
                    if (response.redirected) {
                        window.location.href = response.url;
                    } else if (response.ok) {
                        Swal.fire({
                            toast: true,
                            position: 'bottom-end',
                            icon: 'success',
                            title: 'Enviado com sucesso!',
                            showConfirmButton: false,
                            timer: 3000,
                            timerProgressBar: true,
                        });
                        e.target.reset();
                        document.getElementById('contador').textContent = '300'
                    } else {
                        throw new Error('Erro no envio');
                    }
                })
                .catch(error => {
                    Swal.fire({
                        icon: 'error',
                        title: 'Erro',
                        text: 'Ocorreu um erro ao enviar o feedback.',
                    });
                });
        }
    });
});

document.getElementById('cancelar').addEventListener('click', () => {
    document.getElementById('contador').textContent = '300'
})

if (localStorage.getItem('modo-escuro') === 'true') {
    document.body.classList.add('modo-escuro')
}